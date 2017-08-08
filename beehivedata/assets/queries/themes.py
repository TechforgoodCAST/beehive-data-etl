

def themes_query():
    return [
        {
            "$unwind": "$beehive.themes"
        }, {
            "$group": {
                "_id": {
                    "fund_slug": "$fund_slug",
                    "theme": "$beehive.themes"
                },
                "count": {"$sum": 1}
            }
        }, {
            "$sort": {"count": -1}
        }, {
            "$group": {
                "_id": "$_id.fund_slug",
                "themes": {
                    "$push": {
                        "theme": "$_id.theme",
                        "count": "$count"
                    }
                }
            }
        }, {
            "$sort": {"_id": 1}
        }
    ]
