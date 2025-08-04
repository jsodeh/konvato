"""
Enhanced browser automation manager with parallel processing capabilities.
Implements browser instance pooling, concurrent operations, and resource management.
"""

import os
import json
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
import threading
import psutil
import gc
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from models import Selection, ConversionResult, BookmakerConfig, validate_betslip_code
from bookmaker_adapters import get_bookmaker_adapter, BookmakerAdapter
from browser_manager import BrowserUseManager

# Load environment variables
load_dotenv()

@dataclass
class BrowserInstance:
    """Represents a browser instance in the pool"""
    id: str
    agent: Agent
    in_use: bool
    created_at: datetime
    last_used: datetime
    usage_count: int
    max_usage: int = 50  # Recycle after 50 uses to prevent memory leaks

@dataclass
class ConversionTask:
    """Represents a conversion task in the queue"""
    task_id: str
    betslip_code: str
    source_bookmaker: str
    destination_bookmaker: str
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class BrowserInstancePool:
    """Manages a pool of browser instances for concurrent operations"""
    
    def __init__(self, max_instances: int = 5, max_memory_mb: int = 2048):
        self.max_instances = max_instances
        self.max_memory_mb = max_memory_mb
        self.instances: Dict[str, BrowserInstance] = {}
        self.available_instances = Queue()
        self.lock = threading.Lock()
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        # Initialize LLM based on provider
        provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
        if provider == 'anthropic':
            self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
            
            self.llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=self.anthropic_api_key,
                temperature=0.1,
                max_tokens=1024,  # Reduced for faster responses
                request_timeout=20,  # Faster timeout for parallel operations
                max_retries=1  # Single retry for speed
            )
        else:  # Default to OpenAI
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            
            self.llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.openai_api_key,
                temperature=0.1,
                max_tokens=1024,  # Reduced for faster responses
                request_timeout=20,  # Faster timeout for parallel operations
                max_retries=1  # Single retry for speed
            )
    
    async def get_instance(self) -> BrowserInstance:
        """Get an available browser instance from the pool"""
        with self.lock:
            # Try to get an available instance
            try:
                instance_id = self.available_instances.get_nowait()
                instance = self.instances[instance_id]
                instance.in_use = True
                instance.last_used = datetime.now()
                return instance
            except Empty:
                pass
            
            # If no available instances and we haven't reached the limit, create a new one
            if len(self.instances) < self.max_instances:
                return await self._create_instance()
            
            # If we've reached the limit, wait for an instance to become available
            # This is a simplified approach - in production, you might want a more sophisticated queue
            raise Exception("No browser instances available and pool is at maximum capacity")
    
    async def _create_instance(self) -> BrowserInstance:
        """Create a new browser instance"""
        instance_id = f"browser_{len(self.instances)}_{int(time.time())}"
        
        # Create browser-use agent with optimized configuration
        agent = Agent(
            task="",  # Task will be set when using the instance
            llm=self.llm,
            browser_config={
                "headless": True,
                "stealth": True,
                "timeout": 30000,
                "viewport": {"width": 1280, "height": 720},
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-images",  # Faster loading
                    "--disable-css",     # Skip CSS for speed
                    "--disable-javascript-harmony-shipping",
                    "--memory-pressure-off",
                    "--max_old_space_size=256",  # Further reduced memory
                    "--aggressive-cache-discard",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--disable-default-apps",
                    "--disable-sync"
                ]
            }
        )
        
        instance = BrowserInstance(
            id=instance_id,
            agent=agent,
            in_use=True,
            created_at=datetime.now(),
            last_used=datetime.now(),
            usage_count=0
        )
        
        self.instances[instance_id] = instance
        print(f"Created new browser instance: {instance_id}")
        return instance
    
    def release_instance(self, instance: BrowserInstance):
        """Release a browser instance back to the pool"""
        with self.lock:
            instance.in_use = False
            instance.usage_count += 1
            
            # Check if instance should be recycled
            if instance.usage_count >= instance.max_usage:
                self._recycle_instance(instance)
            else:
                self.available_instances.put(instance.id)
    
    def _recycle_instance(self, instance: BrowserInstance):
        """Recycle an overused browser instance"""
        try:
            # Close the browser instance
            if hasattr(instance.agent, 'browser') and instance.agent.browser:
                asyncio.create_task(instance.agent.browser.close())
            
            # Remove from instances
            del self.instances[instance.id]
            print(f"Recycled browser instance: {instance.id}")
            
        except Exception as e:
            print(f"Error recycling browser instance {instance.id}: {e}")
    
    def cleanup_instances(self):
        """Clean up unused and old instances"""
        current_time = time.time()
        
        # Only run cleanup every cleanup_interval seconds
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        with self.lock:
            instances_to_remove = []
            
            for instance_id, instance in self.instances.items():
                # Remove instances that haven't been used in 30 minutes
                if not instance.in_use and (datetime.now() - instance.last_used).seconds > 1800:
                    instances_to_remove.append(instance_id)
            
            for instance_id in instances_to_remove:
                instance = self.instances[instance_id]
                self._recycle_instance(instance)
            
            self.last_cleanup = current_time
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def check_memory_pressure(self) -> bool:
        """Check if we're under memory pressure"""
        return self.get_memory_usage() > self.max_memory_mb
    
    async def shutdown(self):
        """Shutdown all browser instances"""
        with self.lock:
            for instance in self.instances.values():
                try:
                    if hasattr(instance.agent, 'browser') and instance.agent.browser:
                        await instance.agent.browser.close()
                except Exception as e:
                    print(f"Error closing browser instance {instance.id}: {e}")
            
            self.instances.clear()
            
            # Clear the queue
            while not self.available_instances.empty():
                try:
                    self.available_instances.get_nowait()
                except Empty:
                    break

class ConversionQueue:
    """Manages a queue of conversion requests with priority handling"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.queue = Queue(maxsize=max_size)
        self.processing_tasks: Dict[str, ConversionTask] = {}
        self.completed_tasks: Dict[str, Any] = {}
        self.lock = threading.Lock()
    
    def add_task(self, task: ConversionTask) -> bool:
        """Add a task to the queue"""
        try:
            self.queue.put(task, block=False)
            return True
        except:
            return False  # Queue is full
    
    def get_task(self) -> Optional[ConversionTask]:
        """Get the next task from the queue"""
        try:
            task = self.queue.get(timeout=1)
            with self.lock:
                self.processing_tasks[task.task_id] = task
            return task
        except Empty:
            return None
    
    def complete_task(self, task_id: str, result: Any):
        """Mark a task as completed"""
        with self.lock:
            if task_id in self.processing_tasks:
                del self.processing_tasks[task_id]
            self.completed_tasks[task_id] = result
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task"""
        with self.lock:
            return self.completed_tasks.get(task_id)
    
    def get_queue_size(self) -> int:
        """Get the current queue size"""
        return self.queue.qsize()
    
    def get_processing_count(self) -> int:
        """Get the number of tasks currently being processed"""
        with self.lock:
            return len(self.processing_tasks)

class ParallelBrowserManager(BrowserUseManager):
    """Enhanced browser manager with parallel processing capabilities"""
    
    def __init__(self, openai_api_key: str = None, max_concurrent: int = 3, max_memory_mb: int = 2048):
        super().__init__(openai_api_key)
        
        self.max_concurrent = max_concurrent
        self.browser_pool = BrowserInstancePool(max_instances=max_concurrent, max_memory_mb=max_memory_mb)
        self.conversion_queue = ConversionQueue()
        self.worker_threads = []
        self.shutdown_event = threading.Event()
        
        # Start worker threads
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads for processing conversion requests"""
        for i in range(self.max_concurrent):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(f"worker_{i}",),
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        print(f"Started {self.max_concurrent} worker threads")
    
    def _worker_loop(self, worker_id: str):
        """Main loop for worker threads"""
        print(f"Worker {worker_id} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get a task from the queue
                task = self.conversion_queue.get_task()
                if not task:
                    continue
                
                print(f"Worker {worker_id} processing task {task.task_id}")
                
                # Process the task
                result = asyncio.run(self._process_conversion_task(task))
                
                # Mark task as completed
                self.conversion_queue.complete_task(task.task_id, result)
                
                print(f"Worker {worker_id} completed task {task.task_id}")
                
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                if 'task' in locals():
                    error_result = {
                        'success': False,
                        'error': str(e),
                        'task_id': task.task_id
                    }
                    self.conversion_queue.complete_task(task.task_id, error_result)
            
            # Cleanup and memory management
            gc.collect()
            self.browser_pool.cleanup_instances()
        
        print(f"Worker {worker_id} stopped")
    
    async def _process_conversion_task(self, task: ConversionTask) -> Dict[str, Any]:
        """Process a single conversion task"""
        try:
            # Get a browser instance from the pool
            instance = await self.browser_pool.get_instance()
            
            try:
                # Extract selections from source bookmaker
                selections = await self._extract_selections_with_instance(
                    instance, task.betslip_code, task.source_bookmaker
                )
                
                if not selections:
                    return {
                        'success': False,
                        'error': 'No selections found in betslip',
                        'task_id': task.task_id
                    }
                
                # Create betslip on destination bookmaker
                new_betslip_code = await self._create_betslip_with_instance(
                    instance, selections, task.destination_bookmaker
                )
                
                return {
                    'success': True,
                    'new_betslip_code': new_betslip_code,
                    'converted_selections': [sel.__dict__ for sel in selections],
                    'warnings': [],
                    'task_id': task.task_id,
                    'processing_time': (datetime.now() - task.created_at).total_seconds() * 1000
                }
                
            finally:
                # Always release the instance back to the pool
                self.browser_pool.release_instance(instance)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'task_id': task.task_id
            }
    
    async def _extract_selections_with_instance(self, instance: BrowserInstance, betslip_code: str, bookmaker: str) -> List[Selection]:
        """Extract selections using a specific browser instance"""
        adapter = self._get_bookmaker_adapter(bookmaker)
        config = adapter.config
        
        # Create the extraction task prompt
        task_prompt = f"""
        You are a web automation agent tasked with extracting betting selections from a betslip on {config.name}.
        
        TASK STEPS:
        1. Navigate to {adapter.get_base_url()}
        2. Look for a betslip input field or "Load Betslip" functionality
        3. Enter the betslip code: {betslip_code}
        4. Submit the form or click the load button
        5. Wait for the betslip to load completely
        6. Extract ALL betting selections from the loaded betslip
        
        For each selection, extract:
        - Game/Match name (including team names)
        - Home team name
        - Away team name  
        - Betting market/type (e.g., "Match Result", "Over/Under 2.5", "Both Teams to Score")
        - Odds/Price
        - League/Competition name
        - Event date/time if available
        
        Return the data in JSON format with this structure:
        {{
            "success": true/false,
            "error": "error message if failed",
            "selections": [
                {{
                    "game": "Team A vs Team B",
                    "home_team": "Team A",
                    "away_team": "Team B",
                    "market": "Match Result - Home Win",
                    "odds": 2.50,
                    "league": "Premier League",
                    "event_date": "2024-01-15T15:00:00",
                    "original_text": "original text from the page"
                }}
            ]
        }}
        """
        
        # Update the agent's task
        instance.agent.task = task_prompt
        
        # Execute the extraction
        result = await instance.agent.run()
        
        # Parse the result
        if hasattr(result, 'extracted_content') and result.extracted_content:
            raw_data = result.extracted_content
        elif hasattr(result, 'result') and result.result:
            raw_data = result.result
        else:
            raw_data = str(result)
        
        # Parse the selections
        return self._parse_extracted_data(raw_data, bookmaker)
    
    async def _create_betslip_with_instance(self, instance: BrowserInstance, selections: List[Selection], bookmaker: str) -> str:
        """Create betslip using a specific browser instance"""
        adapter = self._get_bookmaker_adapter(bookmaker)
        config = adapter.config
        
        # Create the betslip creation task prompt
        task_prompt = f"""
        You are a web automation agent tasked with creating a new betslip on {config.name}.
        
        TASK OVERVIEW:
        Create a betslip with the following {len(selections)} selections:
        
        {self._format_selections_for_prompt(selections)}
        
        DETAILED STEPS:
        1. Navigate to {adapter.get_betting_url()}
        2. For each selection above:
           a. Search for the game/match using team names
           b. Navigate to the specific game page
           c. Find and click on the specified betting market
           d. Verify the odds are reasonable (within ±0.10 of expected)
           e. Add the selection to the betslip
        3. Once all selections are added, generate/save the betslip
        4. Extract the betslip code from the generated betslip
        
        Return a JSON response with this structure:
        {{
            "success": true/false,
            "betslip_code": "extracted betslip code",
            "created_selections": [...],
            "skipped_selections": [...],
            "error": "error message if failed"
        }}
        """
        
        # Update the agent's task
        instance.agent.task = task_prompt
        
        # Execute the betslip creation
        result = await instance.agent.run()
        
        # Parse the result
        if hasattr(result, 'extracted_content') and result.extracted_content:
            raw_data = result.extracted_content
        elif hasattr(result, 'result') and result.result:
            raw_data = result.result
        else:
            raw_data = str(result)
        
        # Parse the JSON response
        try:
            if isinstance(raw_data, str):
                raw_data = raw_data.strip()
                if raw_data.startswith('```json'):
                    raw_data = raw_data[7:]
                if raw_data.endswith('```'):
                    raw_data = raw_data[:-3]
                
                parsed_result = json.loads(raw_data)
            else:
                parsed_result = raw_data
            
            if not parsed_result.get('success', False):
                error_msg = parsed_result.get('error', 'Unknown betslip creation error')
                raise Exception(f"Betslip creation failed: {error_msg}")
            
            betslip_code = parsed_result.get('betslip_code', '').strip()
            if not betslip_code:
                raise Exception("No betslip code returned from creation process")
            
            return betslip_code
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse betslip creation response: {str(e)}")
    
    async def convert_betslip_parallel(self, betslip_code: str, source_bookmaker: str, destination_bookmaker: str) -> str:
        """
        Convert a betslip using parallel processing.
        Returns a task ID that can be used to check the result.
        """
        task_id = f"task_{int(time.time())}_{betslip_code}_{source_bookmaker}_{destination_bookmaker}"
        
        task = ConversionTask(
            task_id=task_id,
            betslip_code=betslip_code,
            source_bookmaker=source_bookmaker,
            destination_bookmaker=destination_bookmaker
        )
        
        # Add task to queue
        if not self.conversion_queue.add_task(task):
            raise Exception("Conversion queue is full. Please try again later.")
        
        return task_id
    
    def get_conversion_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a conversion task"""
        return self.conversion_queue.get_result(task_id)
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get the current status of the conversion queue"""
        return {
            'queue_size': self.conversion_queue.get_queue_size(),
            'processing_count': self.conversion_queue.get_processing_count(),
            'active_instances': len([i for i in self.browser_pool.instances.values() if i.in_use]),
            'total_instances': len(self.browser_pool.instances),
            'memory_usage_mb': self.browser_pool.get_memory_usage()
        }
    
    async def process_multiple_selections_parallel(self, selections: List[Selection], bookmaker: str) -> List[Tuple[Selection, bool]]:
        """
        Process multiple betting selections in parallel for faster betslip creation.
        Returns a list of tuples (selection, success_status).
        """
        if not selections:
            return []
        
        # Split selections into batches for parallel processing
        batch_size = min(len(selections), self.max_concurrent)
        batches = [selections[i:i + batch_size] for i in range(0, len(selections), batch_size)]
        
        results = []
        
        for batch in batches:
            # Process each batch in parallel
            tasks = []
            instances = []
            
            try:
                # Get browser instances for this batch
                for _ in batch:
                    instance = await self.browser_pool.get_instance()
                    instances.append(instance)
                
                # Create tasks for parallel execution
                for selection, instance in zip(batch, instances):
                    task = self._process_single_selection(instance, selection, bookmaker)
                    tasks.append(task)
                
                # Execute tasks in parallel
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for selection, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        results.append((selection, False))
                    else:
                        results.append((selection, result))
                
            finally:
                # Release all instances back to the pool
                for instance in instances:
                    self.browser_pool.release_instance(instance)
        
        return results
    
    async def _process_single_selection(self, instance: BrowserInstance, selection: Selection, bookmaker: str) -> bool:
        """Process a single betting selection"""
        try:
            adapter = self._get_bookmaker_adapter(bookmaker)
            
            # Create task for finding and adding this specific selection
            task_prompt = f"""
            Find and add this betting selection to the betslip on {adapter.config.name}:
            
            Game: {selection.home_team} vs {selection.away_team}
            Market: {selection.market}
            Expected Odds: {selection.odds}
            League: {selection.league}
            
            Steps:
            1. Search for the game using team names
            2. Navigate to the game page
            3. Find the specified market
            4. Verify odds are within ±0.10 of expected
            5. Add to betslip
            
            Return JSON: {{"success": true/false, "error": "error message if failed"}}
            """
            
            instance.agent.task = task_prompt
            result = await instance.agent.run()
            
            # Parse result
            if hasattr(result, 'extracted_content'):
                raw_data = result.extracted_content
            else:
                raw_data = str(result)
            
            try:
                parsed = json.loads(raw_data.strip())
                return parsed.get('success', False)
            except:
                return False
                
        except Exception as e:
            print(f"Error processing selection {selection.game_id}: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the parallel browser manager"""
        print("Shutting down parallel browser manager...")
        
        # Signal workers to stop
        self.shutdown_event.set()
        
        # Wait for workers to finish
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        # Shutdown browser pool
        await self.browser_pool.shutdown()
        
        print("Parallel browser manager shutdown complete")

# Export the enhanced manager
__all__ = ['ParallelBrowserManager', 'BrowserInstancePool', 'ConversionQueue']