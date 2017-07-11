

def funders_query():
    return [
        {
            "$group": {
                "_id": {
                    "funder": {"$arrayElemAt": ["$fundingOrganization.slug", 0]},
                    "funder_name": {"$arrayElemAt": ["$fundingOrganization.name", 0]},
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
                    "funder_name": "$_id.funder_name",
                    "fund": "$_id.fund",
                    "fund_name": "$_id.fund_name",
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
            "$sort": {
                "funder": 1,
                "fund": 1
            }
        }, {
            "$group": {
                "_id": {
                    "funder": "$_id.funder",
                    "funder_name": "$_id.funder_name",
                },
                "funds": {
                    "$push": {
                        "fund": "$_id.fund",
                        "fund_name": "$_id.fund_name",
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
                "funder": "$_id.funder",
                "funder_name": "$_id.funder_name",
                "funds": "$funds",
                "count": "$count",
                "sum": "$sum",
            }
        }
    ]
