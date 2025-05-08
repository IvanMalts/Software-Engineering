db = db.getSiblingDB('orders');
db.createCollection("packages");
db.createCollection("delivery");

db.delivery.createIndexes([{sender_id: 1}, {receiver_id: 1}]);
db.packages.createIndex({sender_id: 1});

db.delivery.insertMany([{"_id":1,"package_id":6,"receiver_id":357,"sender_id":496,"address":"51813 Jenifer Lane","deliveryman_id":41,"status":"delivered"},
    {"_id":2,"package_id":3,"receiver_id":774,"sender_id":901,"address":"06412 Truax Street","deliveryman_id":67,"status":"sending"},
    {"_id":3,"package_id":1,"receiver_id":222,"sender_id":90,"address":"8185 Macpherson Way","deliveryman_id":90,"status":"sending"},
    {"_id":4,"package_id":2,"receiver_id":132,"sender_id":176,"address":"49 Oneill Center","deliveryman_id":79,"status":"delivered"},
    {"_id":5,"package_id":5,"receiver_id":22,"sender_id":277,"address":"87466 Dixon Parkway","deliveryman_id":45,"status":"sending"},
    {"_id":6,"package_id":7,"receiver_id":124,"sender_id":434,"address":"880 Elka Point","deliveryman_id":27,"status":"forming"},
    {"_id":7,"package_id":9,"receiver_id":601,"sender_id":265,"address":"142 Center Pass","deliveryman_id":82,"status":"forming"},
    {"_id":8,"package_id":8,"receiver_id":466,"sender_id":494,"address":"9236 Bashford Hill","deliveryman_id":5,"status":"sending"},
    {"_id":9,"package_id":10,"receiver_id":189,"sender_id":689,"address":"5221 Hudson Park","deliveryman_id":43,"status":"delivered"},
    {"_id":10,"package_id":4,"receiver_id":230,"sender_id":207,"address":"47215 Anniversary Place","deliveryman_id":42,"status":"pending"}]);

db.packages.insertMany([{"_id":1,"sender_id":90,"dimensions":354.1,"weight":11.9},
    {"_id":2,"sender_id":176,"dimensions":480.8,"weight":29.7},
    {"_id":3,"sender_id":901,"dimensions":378.6,"weight":92.0},
    {"_id":4,"sender_id":207,"dimensions":182.1,"weight":35.6},
    {"_id":5,"sender_id":277,"dimensions":143.1,"weight":54.0},
    {"_id":6,"sender_id":496,"dimensions":250.0,"weight":20.9},
    {"_id":7,"sender_id":434,"dimensions":342.3,"weight":75.5},
    {"_id":8,"sender_id":494,"dimensions":275.6,"weight":70.4},
    {"_id":9,"sender_id":265,"dimensions":179.2,"weight":52.7},
    {"_id":10,"sender_id":689,"dimensions":257.4,"weight":97.2}]);