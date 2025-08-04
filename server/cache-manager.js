const mongoose = require('mongoose');

// MongoDB Schemas for caching
const gameMappingSchema = new mongoose.Schema({
    sourceBookmaker: { type: String, required: true },
    destinationBookmaker: { type: String, required: true },
    sourceGameId: { type: String, required: true },
    destinationGameId: { type: String, required: true },
    homeTeam: { type: String, required: true },
    awayTeam: { type: String, required: true },
    league: { type: String, required: true },
    eventDate: { type: Date, required: true },
    createdAt: { type: Date, default: Date.now, expires: 86400 } // 24 hour TTL
});

const oddsDataSchema = new mongoose.Schema({
    bookmaker: { type: String, required: true },
    gameId: { type: String, required: true },
    market: { type: String, required: true },
    odds: { type: Number, required: true },
    lastUpdated: { type: Date, default: Date.now },
    createdAt: { type: Date, default: Date.now, expires: 300 } // 5 minute TTL
});

const bookmakerConfigSchema = new mongoose.Schema({
    bookmaker: { type: String, required: true, unique: true },
    config: { type: mongoose.Schema.Types.Mixed, required: true },
    lastUpdated: { type: Date, default: Date.now },
    createdAt: { type: Date, default: Date.now, expires: 604800 } // 1 week TTL
});

const conversionResultSchema = new mongoose.Schema({
    betslipCode: { type: String, required: true }, // This will be '[REDACTED]' for privacy
    sourceBookmaker: { type: String, required: true },
    destinationBookmaker: { type: String, required: true },
    result: { type: mongoose.Schema.Types.Mixed, required: true }, // Sanitized result
    processingTime: { type: Number, required: true },
    createdAt: { type: Date, default: Date.now, expires: 86400 } // 24 hour TTL for compliance
});

// Create indexes for better performance
gameMappingSchema.index({ sourceBookmaker: 1, destinationBookmaker: 1, sourceGameId: 1 });
oddsDataSchema.index({ bookmaker: 1, gameId: 1, market: 1 });
bookmakerConfigSchema.index({ bookmaker: 1 });
conversionResultSchema.index({ betslipCode: 1, sourceBookmaker: 1, destinationBookmaker: 1 });

// Models
const GameMapping = mongoose.model('GameMapping', gameMappingSchema);
const OddsData = mongoose.model('OddsData', oddsDataSchema);
const BookmakerConfig = mongoose.model('BookmakerConfig', bookmakerConfigSchema);
const ConversionResult = mongoose.model('ConversionResult', conversionResultSchema);

// In-memory cache for frequently accessed data
class InMemoryCache {
    constructor() {
        this.cache = new Map();
        this.ttl = new Map();
        
        // Clean up expired entries every 5 minutes
        setInterval(() => this.cleanup(), 300000);
    }
    
    set(key, value, ttlMs = 300000) { // Default 5 minutes TTL
        this.cache.set(key, value);
        this.ttl.set(key, Date.now() + ttlMs);
    }
    
    get(key) {
        if (!this.cache.has(key)) return null;
        
        const expiry = this.ttl.get(key);
        if (Date.now() > expiry) {
            this.cache.delete(key);
            this.ttl.delete(key);
            return null;
        }
        
        return this.cache.get(key);
    }
    
    delete(key) {
        this.cache.delete(key);
        this.ttl.delete(key);
    }
    
    cleanup() {
        const now = Date.now();
        for (const [key, expiry] of this.ttl.entries()) {
            if (now > expiry) {
                this.cache.delete(key);
                this.ttl.delete(key);
            }
        }
    }
    
    clear() {
        this.cache.clear();
        this.ttl.clear();
    }
    
    size() {
        return this.cache.size;
    }
}

class CacheManager {
    constructor() {
        this.inMemoryCache = new InMemoryCache();
        this.isConnected = false;
        this.connectionPromise = null;
    }
    
    async connect() {
        if (this.isConnected) return;
        if (this.connectionPromise) return this.connectionPromise;
        
        this.connectionPromise = this._connect();
        return this.connectionPromise;
    }
    
    async _connect() {
        try {
            const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/betslip-converter';
            await mongoose.connect(mongoUri, {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                maxPoolSize: 10,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000,
            });
            
            this.isConnected = true;
            console.log('Connected to MongoDB for caching');
            
            // Warm up cache with frequently accessed data
            await this.warmUpCache();
            
            // Schedule periodic data retention cleanup (every 6 hours)
            setInterval(() => {
                this.enforceDataRetention().catch(error => {
                    console.error('Scheduled data retention cleanup failed:', error.message);
                });
            }, 6 * 60 * 60 * 1000); // 6 hours
            
        } catch (error) {
            console.error('Failed to connect to MongoDB:', error.message);
            // Continue without MongoDB caching, use only in-memory cache
        }
    }
    
    async warmUpCache() {
        try {
            // Cache bookmaker configurations with longer TTL for frequently used data
            const configs = await BookmakerConfig.find({}).lean();
            for (const config of configs) {
                const key = `bookmaker_config:${config.bookmaker}`;
                this.inMemoryCache.set(key, config.config, 7200000); // 2 hours TTL for configs
            }
            
            // Pre-cache popular bookmaker combinations
            const popularCombinations = [
                ['bet9ja', 'sportybet'],
                ['sportybet', 'bet9ja'],
                ['bet9ja', 'betway'],
                ['betway', 'bet9ja'],
                ['sportybet', 'betway'],
                ['betway', 'sportybet']
            ];
            
            for (const [source, dest] of popularCombinations) {
                const mappingKey = `popular_mapping:${source}:${dest}`;
                this.inMemoryCache.set(mappingKey, { preloaded: true }, 3600000); // 1 hour
            }
            
            // Cache frequently accessed market mappings
            const commonMarkets = [
                'Match Result', '1X2', 'Over/Under 2.5', 'Both Teams to Score',
                'Double Chance', 'Handicap', 'Total Goals', 'First Half Result'
            ];
            
            for (const market of commonMarkets) {
                const marketKey = `common_market:${market.toLowerCase()}`;
                this.inMemoryCache.set(marketKey, { market, cached: true }, 1800000); // 30 minutes
            }
            
            console.log(`Warmed up cache with ${configs.length} bookmaker configurations and ${popularCombinations.length} popular combinations`);
            
        } catch (error) {
            console.error('Cache warm-up failed:', error.message);
        }
    }
    
    // Game mapping cache methods with intelligent TTL
    async cacheGameMapping(sourceBookmaker, destinationBookmaker, sourceGameId, destinationGameId, gameData) {
        const key = `game_mapping:${sourceBookmaker}:${destinationBookmaker}:${sourceGameId}`;
        
        // Determine TTL based on bookmaker popularity and event timing
        let ttl = 86400000; // Default 24 hours
        
        // Popular bookmaker combinations get longer cache
        const popularCombos = ['bet9ja:sportybet', 'sportybet:bet9ja', 'bet9ja:betway', 'betway:bet9ja'];
        const comboKey = `${sourceBookmaker}:${destinationBookmaker}`;
        if (popularCombos.includes(comboKey)) {
            ttl = 172800000; // 48 hours for popular combinations
        }
        
        // Events happening soon get shorter cache to ensure freshness
        if (gameData.eventDate) {
            const eventTime = new Date(gameData.eventDate).getTime();
            const now = Date.now();
            const hoursUntilEvent = (eventTime - now) / (1000 * 60 * 60);
            
            if (hoursUntilEvent < 2) {
                ttl = 1800000; // 30 minutes for events starting soon
            } else if (hoursUntilEvent < 6) {
                ttl = 7200000; // 2 hours for events starting within 6 hours
            }
        }
        
        // Cache in memory with intelligent TTL
        this.inMemoryCache.set(key, { destinationGameId, ...gameData, cachedAt: Date.now() }, ttl);
        
        // Cache in MongoDB if connected
        if (this.isConnected) {
            try {
                await GameMapping.findOneAndUpdate(
                    { sourceBookmaker, destinationBookmaker, sourceGameId },
                    {
                        destinationGameId,
                        homeTeam: gameData.homeTeam,
                        awayTeam: gameData.awayTeam,
                        league: gameData.league,
                        eventDate: gameData.eventDate,
                        popularity: popularCombos.includes(comboKey) ? 'high' : 'normal'
                    },
                    { upsert: true, new: true }
                );
            } catch (error) {
                console.error('Failed to cache game mapping in MongoDB:', error.message);
            }
        }
    }
    
    async getGameMapping(sourceBookmaker, destinationBookmaker, sourceGameId) {
        const key = `game_mapping:${sourceBookmaker}:${destinationBookmaker}:${sourceGameId}`;
        
        // Check in-memory cache first
        let result = this.inMemoryCache.get(key);
        if (result) {
            this.recordCacheHit();
            return result;
        }
        
        // Check MongoDB if connected
        if (this.isConnected) {
            try {
                const mapping = await GameMapping.findOne({
                    sourceBookmaker,
                    destinationBookmaker,
                    sourceGameId
                }).lean();
                
                if (mapping) {
                    result = {
                        destinationGameId: mapping.destinationGameId,
                        homeTeam: mapping.homeTeam,
                        awayTeam: mapping.awayTeam,
                        league: mapping.league,
                        eventDate: mapping.eventDate
                    };
                    
                    // Determine TTL based on popularity
                    const popularCombos = ['bet9ja:sportybet', 'sportybet:bet9ja', 'bet9ja:betway', 'betway:bet9ja'];
                    const comboKey = `${sourceBookmaker}:${destinationBookmaker}`;
                    const ttl = popularCombos.includes(comboKey) ? 172800000 : 86400000;
                    
                    // Cache in memory for faster access
                    this.inMemoryCache.set(key, result, ttl);
                    this.recordCacheHit();
                    return result;
                }
            } catch (error) {
                console.error('Failed to retrieve game mapping from MongoDB:', error.message);
            }
        }
        
        this.recordCacheMiss();
        return null;
    }
    
    // Odds data cache methods with dynamic TTL
    async cacheOddsData(bookmaker, gameId, market, odds, eventDate = null) {
        const key = `odds:${bookmaker}:${gameId}:${market}`;
        
        // Dynamic TTL based on market volatility and event timing
        let ttl = 300000; // Default 5 minutes
        
        // Popular markets get shorter TTL for freshness
        const volatileMarkets = ['match result', '1x2', 'over/under 2.5'];
        if (volatileMarkets.some(vm => market.toLowerCase().includes(vm))) {
            ttl = 180000; // 3 minutes for volatile markets
        }
        
        // Events starting soon need fresher odds
        if (eventDate) {
            const eventTime = new Date(eventDate).getTime();
            const now = Date.now();
            const hoursUntilEvent = (eventTime - now) / (1000 * 60 * 60);
            
            if (hoursUntilEvent < 1) {
                ttl = 60000; // 1 minute for events starting within an hour
            } else if (hoursUntilEvent < 3) {
                ttl = 120000; // 2 minutes for events starting within 3 hours
            }
        }
        
        // Cache in memory with dynamic TTL
        this.inMemoryCache.set(key, { 
            odds, 
            lastUpdated: new Date(),
            volatility: volatileMarkets.some(vm => market.toLowerCase().includes(vm)) ? 'high' : 'normal'
        }, ttl);
        
        // Cache in MongoDB if connected
        if (this.isConnected) {
            try {
                await OddsData.findOneAndUpdate(
                    { bookmaker, gameId, market },
                    { 
                        odds, 
                        lastUpdated: new Date(),
                        eventDate: eventDate,
                        volatility: volatileMarkets.some(vm => market.toLowerCase().includes(vm)) ? 'high' : 'normal'
                    },
                    { upsert: true, new: true }
                );
            } catch (error) {
                console.error('Failed to cache odds data in MongoDB:', error.message);
            }
        }
    }
    
    async getOddsData(bookmaker, gameId, market) {
        const key = `odds:${bookmaker}:${gameId}:${market}`;
        
        // Check in-memory cache first
        let result = this.inMemoryCache.get(key);
        if (result) return result;
        
        // Check MongoDB if connected
        if (this.isConnected) {
            try {
                const oddsData = await OddsData.findOne({
                    bookmaker,
                    gameId,
                    market
                }).lean();
                
                if (oddsData) {
                    result = {
                        odds: oddsData.odds,
                        lastUpdated: oddsData.lastUpdated
                    };
                    
                    // Cache in memory for faster access
                    this.inMemoryCache.set(key, result, 300000);
                    return result;
                }
            } catch (error) {
                console.error('Failed to retrieve odds data from MongoDB:', error.message);
            }
        }
        
        return null;
    }
    
    // Bookmaker configuration cache methods
    async cacheBookmakerConfig(bookmaker, config) {
        const key = `bookmaker_config:${bookmaker}`;
        
        // Cache in memory
        this.inMemoryCache.set(key, config, 3600000); // 1 hour
        
        // Cache in MongoDB if connected
        if (this.isConnected) {
            try {
                await BookmakerConfig.findOneAndUpdate(
                    { bookmaker },
                    { config, lastUpdated: new Date() },
                    { upsert: true, new: true }
                );
            } catch (error) {
                console.error('Failed to cache bookmaker config in MongoDB:', error.message);
            }
        }
    }
    
    async getBookmakerConfig(bookmaker) {
        const key = `bookmaker_config:${bookmaker}`;
        
        // Check in-memory cache first
        let result = this.inMemoryCache.get(key);
        if (result) return result;
        
        // Check MongoDB if connected
        if (this.isConnected) {
            try {
                const config = await BookmakerConfig.findOne({ bookmaker }).lean();
                
                if (config) {
                    result = config.config;
                    
                    // Cache in memory for faster access
                    this.inMemoryCache.set(key, result, 3600000);
                    return result;
                }
            } catch (error) {
                console.error('Failed to retrieve bookmaker config from MongoDB:', error.message);
            }
        }
        
        return null;
    }
    
    // Conversion result cache methods
    async cacheConversionResult(betslipCode, sourceBookmaker, destinationBookmaker, result, processingTime) {
        // Use sanitized key for privacy - never store actual betslip codes
        const sanitizedKey = `conversion:[REDACTED]:${sourceBookmaker}:${destinationBookmaker}`;
        
        // Cache in memory with short TTL
        this.inMemoryCache.set(sanitizedKey, { result, processingTime }, 1800000); // 30 minutes
        
        // Cache in MongoDB if connected (with sanitized data)
        if (this.isConnected) {
            try {
                await ConversionResult.findOneAndUpdate(
                    { betslipCode: '[REDACTED]', sourceBookmaker, destinationBookmaker },
                    { result, processingTime },
                    { upsert: true, new: true }
                );
            } catch (error) {
                console.error('Failed to cache conversion result in MongoDB:', error.message);
            }
        }
    }
    
    async getConversionResult(betslipCode, sourceBookmaker, destinationBookmaker) {
        // Use sanitized key for privacy - we don't cache by actual betslip codes
        const sanitizedKey = `conversion:[REDACTED]:${sourceBookmaker}:${destinationBookmaker}`;
        
        // Check in-memory cache first
        let result = this.inMemoryCache.get(sanitizedKey);
        if (result) return result;
        
        // Check MongoDB if connected (using sanitized data)
        if (this.isConnected) {
            try {
                const cached = await ConversionResult.findOne({
                    betslipCode: '[REDACTED]',
                    sourceBookmaker,
                    destinationBookmaker
                }).lean();
                
                if (cached) {
                    result = {
                        result: cached.result,
                        processingTime: cached.processingTime
                    };
                    
                    // Cache in memory for faster access
                    this.inMemoryCache.set(sanitizedKey, result, 1800000);
                    return result;
                }
            } catch (error) {
                console.error('Failed to retrieve conversion result from MongoDB:', error.message);
            }
        }
        
        return null;
    }
    
    // Cache invalidation methods
    async invalidateGameMappings(sourceBookmaker, destinationBookmaker) {
        // Clear from in-memory cache
        for (const key of this.inMemoryCache.cache.keys()) {
            if (key.startsWith(`game_mapping:${sourceBookmaker}:${destinationBookmaker}:`)) {
                this.inMemoryCache.delete(key);
            }
        }
        
        // Clear from MongoDB if connected
        if (this.isConnected) {
            try {
                await GameMapping.deleteMany({ sourceBookmaker, destinationBookmaker });
            } catch (error) {
                console.error('Failed to invalidate game mappings in MongoDB:', error.message);
            }
        }
    }
    
    async invalidateOddsData(bookmaker, gameId = null) {
        // Clear from in-memory cache
        const pattern = gameId ? `odds:${bookmaker}:${gameId}:` : `odds:${bookmaker}:`;
        for (const key of this.inMemoryCache.cache.keys()) {
            if (key.startsWith(pattern)) {
                this.inMemoryCache.delete(key);
            }
        }
        
        // Clear from MongoDB if connected
        if (this.isConnected) {
            try {
                const query = gameId ? { bookmaker, gameId } : { bookmaker };
                await OddsData.deleteMany(query);
            } catch (error) {
                console.error('Failed to invalidate odds data in MongoDB:', error.message);
            }
        }
    }
    
    // Enhanced cache statistics with performance metrics
    getCacheStats() {
        const stats = {
            inMemorySize: this.inMemoryCache.size(),
            mongoConnected: this.isConnected,
            uptime: process.uptime()
        };
        
        // Add cache hit/miss tracking if available
        if (this.cacheMetrics) {
            stats.hitRate = this.cacheMetrics.hits / (this.cacheMetrics.hits + this.cacheMetrics.misses) || 0;
            stats.totalRequests = this.cacheMetrics.hits + this.cacheMetrics.misses;
            stats.hits = this.cacheMetrics.hits;
            stats.misses = this.cacheMetrics.misses;
        }
        
        return stats;
    }
    
    // Initialize cache metrics tracking
    initializeCacheMetrics() {
        this.cacheMetrics = {
            hits: 0,
            misses: 0,
            lastReset: Date.now()
        };
    }
    
    // Track cache hit
    recordCacheHit() {
        if (!this.cacheMetrics) this.initializeCacheMetrics();
        this.cacheMetrics.hits++;
    }
    
    // Track cache miss
    recordCacheMiss() {
        if (!this.cacheMetrics) this.initializeCacheMetrics();
        this.cacheMetrics.misses++;
    }
    
    // Reset cache metrics
    resetCacheMetrics() {
        this.cacheMetrics = {
            hits: 0,
            misses: 0,
            lastReset: Date.now()
        };
    }
    
    // Data retention compliance methods
    async enforceDataRetention() {
        if (!this.isConnected) return;
        
        try {
            const now = new Date();
            const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            
            // Clean up expired conversion results (older than 24 hours)
            const deletedConversions = await ConversionResult.deleteMany({
                createdAt: { $lt: oneDayAgo }
            });
            
            // Clean up old game mappings (older than 24 hours)
            const deletedMappings = await GameMapping.deleteMany({
                createdAt: { $lt: oneDayAgo }
            });
            
            // Clean up old odds data (older than 5 minutes is handled by TTL)
            // Clean up old bookmaker configs (older than 1 week)
            const deletedConfigs = await BookmakerConfig.deleteMany({
                createdAt: { $lt: oneWeekAgo }
            });
            
            console.log(`Data retention cleanup completed: ${deletedConversions.deletedCount} conversions, ${deletedMappings.deletedCount} mappings, ${deletedConfigs.deletedCount} configs deleted`);
            
        } catch (error) {
            console.error('Data retention cleanup failed:', error.message);
        }
    }
    
    // Cleanup method
    async cleanup() {
        // Perform final data retention cleanup
        await this.enforceDataRetention();
        
        this.inMemoryCache.clear();
        if (this.isConnected) {
            await mongoose.connection.close();
            this.isConnected = false;
        }
    }
}

// Export singleton instance
const cacheManager = new CacheManager();

module.exports = cacheManager;