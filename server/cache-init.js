const cacheManager = require('./cache-manager');

/**
 * Initialize cache with bookmaker configurations
 * This script can be run independently or called from the main server
 */

const bookmakerConfigurations = {
    bet9ja: {
        id: "bet9ja",
        name: "Bet9ja",
        base_url: "https://www.bet9ja.com",
        betslip_url_pattern: "https://www.bet9ja.com/betslip/{code}",
        betting_url: "https://www.bet9ja.com/sport",
        dom_selectors: {
            betslip_input: "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
            submit_button: "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip",
            betslip_form: "form[action*='betslip'], .betslip-form, #betslip-form",
            selections_container: ".betslip-selections, .selections, .bet-items, .coupon-items, .slip-content",
            selection_item: ".selection, .bet-item, .coupon-item, .match-item, .slip-item",
            game_name: ".match-name, .game-name, .event-name, .teams, .match-title",
            market_name: ".market, .bet-type, .selection-type, .market-name",
            odds: ".odds, .odd, .price, .odds-value",
            league: ".league, .competition, .tournament",
            event_date: ".date, .time, .event-time, .match-time",
            search_box: "input[placeholder*='search'], input[name*='search'], .search-input, #search",
            search_button: "button[type='submit'], .search-btn, .search-button",
            game_links: ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game']",
            market_buttons: ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn",
            add_to_betslip: ".add-to-betslip, .add-bet, button[data-add], .add-selection",
            betslip_area: ".betslip, .bet-slip, .coupon, #betslip, .slip-container",
            betslip_code_display: ".betslip-code, .share-code, .reference-code, .coupon-id, .slip-id"
        },
        market_mappings: {
            "match result": "1X2",
            "1x2": "1X2",
            "over/under 2.5": "Over/Under 2.5 Goals",
            "both teams to score": "Both Teams To Score",
            "double chance": "Double Chance",
            "handicap": "Handicap",
            "correct score": "Correct Score",
            "total goals": "Total Goals",
            "first half result": "1st Half Result",
            "half time/full time": "Half Time/Full Time"
        },
        team_name_normalizations: {
            "Manchester United": "Man United",
            "Manchester City": "Man City",
            "Tottenham Hotspur": "Tottenham",
            "Brighton & Hove Albion": "Brighton",
            "West Ham United": "West Ham",
            "Newcastle United": "Newcastle",
            "Wolverhampton Wanderers": "Wolves",
            "Leicester City": "Leicester",
            "Crystal Palace": "C Palace",
            "Sheffield United": "Sheffield Utd",
            "Real Madrid": "R Madrid",
            "Atletico Madrid": "A Madrid",
            "Bayern Munich": "Bayern",
            "Borussia Dortmund": "B Dortmund",
            "Paris Saint-Germain": "PSG",
            "AC Milan": "Milan",
            "Inter Milan": "Inter"
        },
        supported: true
    },
    
    sportybet: {
        id: "sportybet",
        name: "SportyBet",
        base_url: "https://www.sportybet.com",
        betslip_url_pattern: "https://www.sportybet.com/ng/sport/betslip/{code}",
        betting_url: "https://www.sportybet.com/ng/sport",
        dom_selectors: {
            betslip_input: "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
            submit_button: "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip, .btn-primary",
            betslip_form: "form[action*='betslip'], .betslip-form, #betslip-form",
            selections_container: ".betslip-selections, .selections, .bet-items, .coupon-items, .betslip-content",
            selection_item: ".selection, .bet-item, .coupon-item, .match-item, .betslip-item",
            game_name: ".match-name, .game-name, .event-name, .teams, .match-title, .event-title",
            market_name: ".market, .bet-type, .selection-type, .market-name, .bet-name",
            odds: ".odds, .odd, .price, .odds-value, .rate",
            league: ".league, .competition, .tournament, .league-name",
            event_date: ".date, .time, .event-time, .match-time, .start-time",
            search_box: "input[placeholder*='search'], input[name*='search'], .search-input, #search, .search-field",
            search_button: "button[type='submit'], .search-btn, .search-button, .btn-search",
            game_links: ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game'], .event-item",
            market_buttons: ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn, .odd-btn",
            add_to_betslip: ".add-to-betslip, .add-bet, button[data-add], .add-selection, .add-to-slip",
            betslip_area: ".betslip, .bet-slip, .coupon, #betslip, .slip-container, .betslip-panel",
            betslip_code_display: ".betslip-code, .share-code, .reference-code, .coupon-id, .slip-id, .booking-code"
        },
        market_mappings: {
            "match result": "Match Result",
            "1x2": "Match Result",
            "over/under 2.5": "Total Goals Over/Under 2.5",
            "both teams to score": "Both Teams To Score",
            "double chance": "Double Chance",
            "handicap": "Asian Handicap",
            "correct score": "Correct Score",
            "total goals": "Total Goals",
            "first half result": "1st Half Result",
            "half time/full time": "Half Time/Full Time",
            "draw no bet": "Draw No Bet",
            "goal line": "Goal Line"
        },
        team_name_normalizations: {
            "Manchester United": "Manchester Utd",
            "Manchester City": "Man City",
            "Tottenham Hotspur": "Tottenham",
            "Brighton & Hove Albion": "Brighton",
            "West Ham United": "West Ham",
            "Newcastle United": "Newcastle",
            "Wolverhampton Wanderers": "Wolverhampton",
            "Leicester City": "Leicester",
            "Crystal Palace": "Crystal Palace",
            "Sheffield United": "Sheffield Utd",
            "Real Madrid": "Real Madrid",
            "Atletico Madrid": "Atletico Madrid",
            "Bayern Munich": "Bayern Munich",
            "Borussia Dortmund": "Dortmund",
            "Paris Saint-Germain": "Paris SG",
            "AC Milan": "AC Milan",
            "Inter Milan": "Inter Milan"
        },
        supported: true
    },
    
    betway: {
        id: "betway",
        name: "Betway",
        base_url: "https://www.betway.com",
        betslip_url_pattern: "https://www.betway.com/betslip/{code}",
        betting_url: "https://www.betway.com/sport",
        dom_selectors: {
            betslip_input: "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
            submit_button: "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip, .btn-primary",
            betslip_form: "form[action*='betslip'], .betslip-form, #betslip-form",
            selections_container: ".betslip-selections, .selections, .bet-items, .coupon-items, .betslip-wrapper",
            selection_item: ".selection, .bet-item, .coupon-item, .match-item, .betslip-selection",
            game_name: ".match-name, .game-name, .event-name, .teams, .match-title, .fixture-name",
            market_name: ".market, .bet-type, .selection-type, .market-name, .outcome-name",
            odds: ".odds, .odd, .price, .odds-value, .decimal-odds",
            league: ".league, .competition, .tournament, .competition-name",
            event_date: ".date, .time, .event-time, .match-time, .kick-off-time",
            search_box: "input[placeholder*='search'], input[name*='search'], .search-input, #search, .search-field",
            search_button: "button[type='submit'], .search-btn, .search-button, .search-submit",
            game_links: ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game'], .fixture-link",
            market_buttons: ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn, .outcome-btn",
            add_to_betslip: ".add-to-betslip, .add-bet, button[data-add], .add-selection, .add-to-slip",
            betslip_area: ".betslip, .bet-slip, .coupon, #betslip, .slip-container, .betslip-container",
            betslip_code_display: ".betslip-code, .share-code, .reference-code, .coupon-id, .slip-reference"
        },
        market_mappings: {
            "match result": "Match Result",
            "1x2": "Match Result",
            "over/under 2.5": "Over/Under 2.5 Goals",
            "both teams to score": "Both Teams to Score",
            "double chance": "Double Chance",
            "handicap": "Handicap",
            "correct score": "Correct Score",
            "total goals": "Total Goals",
            "first half result": "First Half Result",
            "half time/full time": "Half Time/Full Time",
            "draw no bet": "Draw No Bet",
            "clean sheet": "Clean Sheet",
            "anytime goalscorer": "Anytime Goalscorer"
        },
        team_name_normalizations: {
            "Manchester United": "Man Utd",
            "Manchester City": "Man City",
            "Tottenham Hotspur": "Tottenham",
            "Brighton & Hove Albion": "Brighton",
            "West Ham United": "West Ham",
            "Newcastle United": "Newcastle",
            "Wolverhampton Wanderers": "Wolves",
            "Leicester City": "Leicester",
            "Crystal Palace": "Crystal Palace",
            "Sheffield United": "Sheffield Utd",
            "Real Madrid": "Real Madrid",
            "Atletico Madrid": "Atletico Madrid",
            "Bayern Munich": "Bayern Munich",
            "Borussia Dortmund": "Borussia Dortmund",
            "Paris Saint-Germain": "PSG",
            "AC Milan": "AC Milan",
            "Inter Milan": "Inter"
        },
        supported: true
    },
    
    bet365: {
        id: "bet365",
        name: "Bet365",
        base_url: "https://www.bet365.com",
        betslip_url_pattern: "https://www.bet365.com/betslip/{code}",
        betting_url: "https://www.bet365.com/sport",
        dom_selectors: {
            betslip_input: "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
            submit_button: "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip",
            betslip_form: "form[action*='betslip'], .betslip-form, #betslip-form",
            selections_container: ".betslip-selections, .selections, .bet-items, .coupon-items, .bss-NormalBetItem_Container",
            selection_item: ".selection, .bet-item, .coupon-item, .match-item, .bss-NormalBetItem",
            game_name: ".match-name, .game-name, .event-name, .teams, .match-title, .bss-NormalBetItem_Title",
            market_name: ".market, .bet-type, .selection-type, .market-name, .bss-NormalBetItem_Market",
            odds: ".odds, .odd, .price, .odds-value, .bss-NormalBetItem_Odds",
            league: ".league, .competition, .tournament, .bss-NormalBetItem_Competition",
            event_date: ".date, .time, .event-time, .match-time, .bss-NormalBetItem_StartTime",
            search_box: "input[placeholder*='search'], input[name*='search'], .search-input, #search",
            search_button: "button[type='submit'], .search-btn, .search-button",
            game_links: ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game'], .sl-CouponParticipantWithBookCloses",
            market_buttons: ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn, .gl-Participant_General",
            add_to_betslip: ".add-to-betslip, .add-bet, button[data-add], .add-selection",
            betslip_area: ".betslip, .bet-slip, .coupon, #betslip, .bss-BetslipContainer",
            betslip_code_display: ".betslip-code, .share-code, .reference-code, .coupon-id, .bss-ShareBetslip_Code"
        },
        market_mappings: {
            "match result": "Result",
            "1x2": "Result",
            "over/under 2.5": "Goals Over/Under",
            "both teams to score": "Both Teams to Score",
            "double chance": "Double Chance",
            "handicap": "Asian Handicap",
            "correct score": "Correct Score",
            "total goals": "Total Goals",
            "first half result": "Half Time Result",
            "half time/full time": "Half Time/Full Time",
            "draw no bet": "Draw No Bet",
            "clean sheet": "To Keep a Clean Sheet",
            "anytime goalscorer": "Goalscorer"
        },
        team_name_normalizations: {
            "Manchester United": "Man Utd",
            "Manchester City": "Man City",
            "Tottenham Hotspur": "Tottenham",
            "Brighton & Hove Albion": "Brighton",
            "West Ham United": "West Ham",
            "Newcastle United": "Newcastle",
            "Wolverhampton Wanderers": "Wolves",
            "Leicester City": "Leicester",
            "Crystal Palace": "Crystal Palace",
            "Sheffield United": "Sheffield Utd",
            "Real Madrid": "Real Madrid",
            "Atletico Madrid": "Atletico Madrid",
            "Bayern Munich": "Bayern Munich",
            "Borussia Dortmund": "Borussia Dortmund",
            "Paris Saint-Germain": "Paris SG",
            "AC Milan": "AC Milan",
            "Inter Milan": "Inter Milan"
        },
        supported: true
    }
};

async function initializeCache() {
    try {
        console.log('Initializing cache with bookmaker configurations...');
        
        // Connect to cache manager
        await cacheManager.connect();
        
        // Cache all bookmaker configurations
        for (const [bookmaker, config] of Object.entries(bookmakerConfigurations)) {
            await cacheManager.cacheBookmakerConfig(bookmaker, config);
            console.log(`Cached configuration for ${bookmaker}`);
        }
        
        console.log('Cache initialization completed successfully');
        
        // Get cache statistics
        const stats = cacheManager.getCacheStats();
        console.log('Cache statistics:', stats);
        
    } catch (error) {
        console.error('Cache initialization failed:', error.message);
        throw error;
    }
}

// Export for use in other modules
module.exports = {
    initializeCache,
    bookmakerConfigurations
};

// Run initialization if this script is executed directly
if (require.main === module) {
    initializeCache()
        .then(() => {
            console.log('Cache initialization script completed');
            process.exit(0);
        })
        .catch((error) => {
            console.error('Cache initialization script failed:', error);
            process.exit(1);
        });
}