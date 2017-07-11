

def amounts_query():
    return [
        {
            "$group": {
                "_id": {
                    "funder": {
                        "$arrayElemAt": ["$fundingOrganization.slug", 0]
                    },
                    "fund": {
                        "$arrayElemAt": ["$grantProgramme.slug", 0]
                    },
                },
                "amounts": {"$push": "$amountAwarded"},
            }
        }, {
            "$project": {
                "_id": 0,
                "fund_slug": {"$concat": ["$_id.funder", "-", "$_id.fund"]},
                "amounts": "$amounts"
            }
        }
    ]
