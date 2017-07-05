
FIELDS_TO_CHECK = [
    # (title, field, is_array)
    ("Age Group", "beehive.ages", True),
    ("Amount Awarded", "amountAwarded", False),
    ("Award Date", "awardDate", False),
    ("Beneficiaries", "beehive.beneficiaries", True),
    ("Country", "beehive.countries", True),
    ("District", "beehive.districts", True),
    ("Duration", "plannedDates.duration", False),
    ("Employees", "beehive.employees", False),
    ("Gender", "beehive.gender", False),
    ("Geographic Scale", "beehive.geographic_scale", False),
    ("Income", "beehive.income", False),
    ("Operating for", "beehive.operating_for", False),
    ("Organisation Type", "beehive.org_type", False),
    ("Sources", "dataset.source", False),
    ("Volunteers", "beehive.volunteers", False),
]


def status_query():

    group = {**{
        f[0]: {
            "$sum": {
                "$cond": [{
                    "$ifNull": ["${}".format(f[1]), False]
                }, 1, 0]
            }
        } for f in FIELDS_TO_CHECK if not f[2]
    }, **{
        f[0]: {
            "$sum": {
                "$cond": [{
                    "$gt": [{
                        "$size": {
                            "$ifNull": ["${}".format(f[1]), []]
                        }
                    }, 0]
                }, 1, 0]
            }
        } for f in FIELDS_TO_CHECK if f[2]
    }}
    group["_id"] = {
        "fund_slug": "$fund_slug",
        "fund": {"$arrayElemAt": ["$grantProgramme.slug", 0]},
        "funder": {"$arrayElemAt": ["$fundingOrganization.name", 0]},
    }
    group["count"] = {"$sum": 1}
    group["sum"] = {"$sum": "$amountAwarded"}

    project = {f[0]: "$%s" % f[0] for f in FIELDS_TO_CHECK}
    project["_id"] = "$_id.fund_slug"
    project["fund"] = "$_id.fund"
    project["funder"] = "$_id.funder"
    project["count"] = "$count"
    project["sum"] = "$sum"

    return [
        {
        #     "$match": {
        #         "awardDate": {"$gt": one_year_before}
        #         # @TODO: also restrict to latest grants
        #     }
        # }, {
            "$group": group
        }, {
            "$project": project
        }, {
            "$sort": {"_id": 1}
        }
    ]


def process_fund(fund):
    for f in FIELDS_TO_CHECK:
        percent = float(fund[f[0]]) / fund["count"]
        if percent == 1:
            feedback = 'positive green'
        elif percent == 0:
            feedback = 'negative red'
        elif percent > 0.5:
            feedback = 'warning olive'
        else:
            feedback = 'warning yellow'
        fund[f[0]] = {
            "percent": percent,
            "feedback": feedback,
            "count": fund[f[0]]
        }
    return fund
