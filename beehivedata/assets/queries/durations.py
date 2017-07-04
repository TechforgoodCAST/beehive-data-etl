

def durations_query():
    return [
        {
            "$unwind": "$plannedDates"
        }, {
            "$group": {
                "_id": {
                    "funder": {
                        "$arrayElemAt": ["$fundingOrganization.slug", 0]
                    },
                    "fund": {
                        "$arrayElemAt": ["$grantProgramme.slug", 0]
                    },
                },
                "durations": {"$push": "$plannedDates.duration"},
            }
        }, {
            "$project": {
                "_id": 0,
                "fund_slug": {"$concat": ["$_id.funder", "-", "$_id.fund"]},
                "durations": "$durations"
            }
        }
    ]
