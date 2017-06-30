

def funders_query():
    return [
        {
            "$group": {
                "_id": {
                    "funder": {"$arrayElemAt": ["$fundingOrganization.slug", 0]},
                    "fund": {"$arrayElemAt": ["$grantProgramme.slug", 0]},
                    "year": {"$year": "$awardDate"},
                },
                "count": {"$sum": 1},
                "sum": {"$sum": "$amountAwarded"},
            }
        }, {
            "$group": {
                "_id": {
                    "funder": "$_id.funder",
                    "fund": "$_id.fund",
                },
                "years": {
                    "$push": {
                        "year": "$_id.year",
                        "count": "$count",
                        "sum": "$sum"
                    }
                },
                "sum": {"$sum": "$sum"},
                "count": {"$sum": "$count"},
            }
        }, {
            "$group": {
                "_id": "$_id.funder",
                "funds": {
                    "$push": {
                        "fund": "$_id.fund",
                        "fund_slug": {"$concat": ["$_id.funder", "-", "$_id.fund"]},
                        "years": "$years",
                        "count": "$count",
                        "sum": "$sum"
                    }

                },
                "count": {"$sum": "$count"},
                "sum": {"$sum": "$sum"},
            }
        }, {
            "$project": {
                "_id": 0,
                "funder": "$_id",
                "funds": "$funds",
                "count": "$count",
                "sum": "$sum",
            }
        }
    ]
