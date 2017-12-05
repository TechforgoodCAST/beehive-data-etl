

def amounts_query():
    return [
        {
            "$group": {
                "_id": "$fund_slug",
                "amounts": {"$push": "$amountAwarded"},
            }
        }, {
            "$project": {
                "_id": 0,
                "fund_slug": "$_id",
                "amounts": "$amounts"
            }
        }
    ]
