const cacheManager = require('./cache-manager');
const { initializeCache } = require('./cache-init');

async function testCaching() {
    console.log('Testing cache functionality...');
    
    try {
        // Initialize cache
        await initializeCache();
        
        // Test bookmaker configuration caching
        console.log('\n1. Testing bookmaker configuration caching...');
        const bet9jaConfig = await cacheManager.getBookmakerConfig('bet9ja');
        console.log('Bet9ja config retrieved:', bet9jaConfig ? 'SUCCESS' : 'FAILED');
        
        // Test game mapping caching
        console.log('\n2. Testing game mapping caching...');
        const gameData = {
            homeTeam: 'Manchester United',
            awayTeam: 'Liverpool',
            league: 'Premier League',
            eventDate: new Date()
        };
        
        await cacheManager.cacheGameMapping('bet9ja', 'sportybet', 'game123', 'game456', gameData);
        const retrievedMapping = await cacheManager.getGameMapping('bet9ja', 'sportybet', 'game123');
        console.log('Game mapping cached and retrieved:', retrievedMapping ? 'SUCCESS' : 'FAILED');
        
        // Test odds data caching
        console.log('\n3. Testing odds data caching...');
        await cacheManager.cacheOddsData('bet9ja', 'game123', 'match_result', 2.50);
        const retrievedOdds = await cacheManager.getOddsData('bet9ja', 'game123', 'match_result');
        console.log('Odds data cached and retrieved:', retrievedOdds ? 'SUCCESS' : 'FAILED');
        
        // Test conversion result caching
        console.log('\n4. Testing conversion result caching...');
        const conversionResult = {
            success: true,
            new_betslip_code: 'ABC123',
            converted_selections: [],
            warnings: []
        };
        
        await cacheManager.cacheConversionResult('TEST123', 'bet9ja', 'sportybet', conversionResult, 5000);
        const retrievedResult = await cacheManager.getConversionResult('TEST123', 'bet9ja', 'sportybet');
        console.log('Conversion result cached and retrieved:', retrievedResult ? 'SUCCESS' : 'FAILED');
        
        // Test cache statistics
        console.log('\n5. Cache statistics:');
        const stats = cacheManager.getCacheStats();
        console.log(JSON.stringify(stats, null, 2));
        
        console.log('\nAll cache tests completed successfully!');
        
    } catch (error) {
        console.error('Cache test failed:', error.message);
        throw error;
    } finally {
        // Cleanup
        await cacheManager.cleanup();
    }
}

// Jest test suite
describe('Cache Functionality', () => {
    test('Cache Operations', async () => {
        await testCaching();
    });
});

module.exports = { testCaching };