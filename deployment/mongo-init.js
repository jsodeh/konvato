// MongoDB initialization script for production deployment

// Switch to the betslip_converter database
db = db.getSiblingDB('betslip_converter');

// Create application user with appropriate permissions
db.createUser({
  user: 'betslip_user',
  pwd: 'betslip_password_change_in_production',
  roles: [
    {
      role: 'readWrite',
      db: 'betslip_converter'
    }
  ]
});

// Create collections with appropriate indexes
db.createCollection('game_mappings');
db.createCollection('bookmaker_configs');
db.createCollection('conversion_cache');
db.createCollection('performance_metrics');

// Create indexes for optimal performance
db.game_mappings.createIndex({ "homeTeam": 1, "awayTeam": 1, "bookmaker": 1 });
db.game_mappings.createIndex({ "createdAt": 1 }, { expireAfterSeconds: 86400 }); // 24 hours TTL

db.bookmaker_configs.createIndex({ "bookmaker": 1 });
db.bookmaker_configs.createIndex({ "lastUpdated": 1 });

db.conversion_cache.createIndex({ "betslipCode": 1, "sourceBookmaker": 1, "destinationBookmaker": 1 });
db.conversion_cache.createIndex({ "createdAt": 1 }, { expireAfterSeconds: 300 }); // 5 minutes TTL

db.performance_metrics.createIndex({ "timestamp": 1 });
db.performance_metrics.createIndex({ "operation": 1, "timestamp": 1 });

// Insert initial bookmaker configurations
db.bookmaker_configs.insertMany([
  {
    bookmaker: "bet9ja",
    name: "Bet9ja",
    baseUrl: "https://www.bet9ja.com",
    betslipUrlPattern: "https://www.bet9ja.com/betslip/{code}",
    bettingUrl: "https://www.bet9ja.com/sport",
    supported: true,
    lastUpdated: new Date(),
    domSelectors: {
      betslipInput: "#betslip-code",
      submitButton: ".submit-betslip",
      selections: ".selection-item",
      odds: ".odds-value"
    },
    marketMappings: {
      "1X2": "Match Result",
      "Over/Under 2.5": "Total Goals Over/Under 2.5",
      "Both Teams to Score": "Both Teams To Score"
    }
  },
  {
    bookmaker: "sportybet",
    name: "SportyBet",
    baseUrl: "https://www.sportybet.com",
    betslipUrlPattern: "https://www.sportybet.com/ng/sport/betslip/{code}",
    bettingUrl: "https://www.sportybet.com/ng/sport",
    supported: true,
    lastUpdated: new Date(),
    domSelectors: {
      betslipInput: ".betslip-code-input",
      submitButton: ".load-betslip",
      selections: ".bet-selection",
      odds: ".odds-display"
    },
    marketMappings: {
      "Match Result": "1X2",
      "Total Goals Over/Under 2.5": "Over/Under 2.5",
      "Both Teams To Score": "Both Teams to Score"
    }
  },
  {
    bookmaker: "betway",
    name: "Betway",
    baseUrl: "https://www.betway.com",
    betslipUrlPattern: "https://www.betway.com/betslip/{code}",
    bettingUrl: "https://www.betway.com/sport",
    supported: true,
    lastUpdated: new Date(),
    domSelectors: {
      betslipInput: "#betslip-reference",
      submitButton: ".view-betslip",
      selections: ".betslip-selection",
      odds: ".selection-odds"
    },
    marketMappings: {
      "Match Winner": "1X2",
      "Total Goals": "Over/Under 2.5",
      "Both Teams Score": "Both Teams to Score"
    }
  },
  {
    bookmaker: "bet365",
    name: "Bet365",
    baseUrl: "https://www.bet365.com",
    betslipUrlPattern: "https://www.bet365.com/betslip/{code}",
    bettingUrl: "https://www.bet365.com/sport",
    supported: true,
    lastUpdated: new Date(),
    domSelectors: {
      betslipInput: ".betslip-code",
      submitButton: ".load-slip",
      selections: ".bet-item",
      odds: ".odds-value"
    },
    marketMappings: {
      "Result": "1X2",
      "Goals Over/Under": "Over/Under 2.5",
      "Both Teams To Score": "Both Teams to Score"
    }
  }
]);

print("MongoDB initialization completed successfully");