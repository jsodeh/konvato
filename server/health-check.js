#!/usr/bin/env node

/**
 * Health check script for betslip converter application
 * Used by Docker healthcheck and monitoring systems
 */

const http = require('http');
const { spawn } = require('child_process');

const HEALTH_CHECK_TIMEOUT = parseInt(process.env.HEALTH_CHECK_TIMEOUT) || 5000;
const PORT = process.env.PORT || 5000;

async function checkServerHealth() {
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: 'localhost',
      port: PORT,
      path: '/api/health',
      method: 'GET',
      timeout: HEALTH_CHECK_TIMEOUT
    }, (res) => {
      if (res.statusCode === 200) {
        resolve({ service: 'server', status: 'healthy' });
      } else {
        reject(new Error(`Server health check failed with status ${res.statusCode}`));
      }
    });

    req.on('error', (err) => {
      reject(new Error(`Server health check failed: ${err.message}`));
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Server health check timed out'));
    });

    req.end();
  });
}

async function checkMongoHealth() {
  return new Promise((resolve, reject) => {
    const mongoose = require('mongoose');
    
    if (mongoose.connection.readyState === 1) {
      resolve({ service: 'mongodb', status: 'healthy' });
    } else {
      reject(new Error('MongoDB connection not ready'));
    }
  });
}

async function checkPythonEnvironment() {
  return new Promise((resolve, reject) => {
    const python = spawn('python3', ['-c', 'import browser_use; import playwright; print("OK")'], {
      timeout: HEALTH_CHECK_TIMEOUT
    });

    let output = '';
    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0 && output.trim() === 'OK') {
        resolve({ service: 'python_automation', status: 'healthy' });
      } else {
        reject(new Error(`Python environment check failed with code ${code}`));
      }
    });

    python.on('error', (err) => {
      reject(new Error(`Python environment check failed: ${err.message}`));
    });
  });
}

async function checkBrowserAutomation() {
  return new Promise((resolve, reject) => {
    const python = spawn('python3', ['-c', `
import asyncio
from playwright.async_api import async_playwright

async def check_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('data:text/html,<h1>Health Check</h1>')
        title = await page.title()
        await browser.close()
        return title

result = asyncio.run(check_browser())
print("Browser OK" if result else "Browser Failed")
`], {
      timeout: HEALTH_CHECK_TIMEOUT * 2
    });

    let output = '';
    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0 && output.includes('Browser OK')) {
        resolve({ service: 'browser_automation', status: 'healthy' });
      } else {
        reject(new Error(`Browser automation check failed`));
      }
    });

    python.on('error', (err) => {
      reject(new Error(`Browser automation check failed: ${err.message}`));
    });
  });
}

async function runHealthChecks() {
  const checks = [
    checkServerHealth(),
    checkMongoHealth(),
    checkPythonEnvironment(),
    checkBrowserAutomation()
  ];

  try {
    const results = await Promise.allSettled(checks);
    const healthStatus = {
      timestamp: new Date().toISOString(),
      overall: 'healthy',
      services: {}
    };

    let hasFailures = false;

    results.forEach((result, index) => {
      const serviceNames = ['server', 'mongodb', 'python_automation', 'browser_automation'];
      const serviceName = serviceNames[index];

      if (result.status === 'fulfilled') {
        healthStatus.services[serviceName] = result.value;
      } else {
        healthStatus.services[serviceName] = {
          service: serviceName,
          status: 'unhealthy',
          error: result.reason.message
        };
        hasFailures = true;
      }
    });

    if (hasFailures) {
      healthStatus.overall = 'degraded';
    }

    // Output results
    console.log(JSON.stringify(healthStatus, null, 2));

    // Exit with appropriate code
    if (healthStatus.overall === 'healthy') {
      process.exit(0);
    } else {
      process.exit(1);
    }

  } catch (error) {
    console.error('Health check failed:', error.message);
    process.exit(1);
  }
}

// Handle script execution
if (require.main === module) {
  runHealthChecks();
}

module.exports = {
  checkServerHealth,
  checkMongoHealth,
  checkPythonEnvironment,
  checkBrowserAutomation,
  runHealthChecks
};