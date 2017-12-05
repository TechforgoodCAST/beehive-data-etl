

def durations_query():
    return [
        {
            "$unwind": "$plannedDates"
        }, {
            "$group": {
                "_id": "$fund_slug",
                "durations": {"$push": "$plannedDates.duration"},
            }
        }, {
            "$project": {
                "_id": 0,
                "fund_slug": "$_id",
                "durations": "$durations"
            }
        }
    ]
