import os
from ..beneficiaries import ben_categories
from ...actions.update_geography import get_countries

DISTRIBUTIONS = {
    "duration_awarded_months_distribution": [
        (0, {"position": 1, "label": "0-3 months"}),
        (3, {"position": 2, "label": "3-6 months"}),
        (6, {"position": 3, "label": "6-12 months"}),
        (12, {"position": 4, "label": "12-18 months"}),
        (18, {"position": 5, "label": "18-24 months"}),
        (24, {"position": 6, "label": "2-3 years"}),
        (36, {"position": 7, "label": "3-3 years"}),
        (48, {"position": 8, "label": "More than 4 years"}),
        (1000, None),
    ],
    "org_type_distribution": [
        (-1, {"position": 1, "label": "An individual"}),
        (0, {"position": 2, "label": "An unregistered organisation OR project"}),
        (1, {"position": 3, "label": "A registered charity"}),
        (2, {"position": 4, "label": "A registered company"}),
        (3, {"position": 5, "label": "A registered charity & company"}),
        (4, {"position": 6, "label": "Another type of organisation"}),
        (5, {"position": 7, "label": "Community Interest Company"}),
    ],
    "income_distribution": [
        (0, {"position": 1, "label": "Less than £10k"}),
        (10000, {"position": 2, "label": "£10k - £100k"}),
        (100000, {"position": 3, "label": "£100k - £1m"}),
        (1000000, {"position": 4, "label": "£1m - £10m"}),
        (10000000, {"position": 5, "label": "£10m+"}),
        ("Unknown", {"position": 6, "label": 'Unknown'}),
        (1000000000, None)
    ],
    "employees_distribution": [
        (0, {"position": 1, "label": "None"}),
        (1, {"position": 2, "label": "1 - 5"}),
        (5, {"position": 3, "label": "6 - 25"}),
        (25, {"position": 4, "label": "26 - 50"}),
        (50, {"position": 5, "label": "51 - 100"}),
        (100, {"position": 6, "label": "101 - 250"}),
        (250, {"position": 7, "label": "251 - 500"}),
        (500, {"position": 8, "label": "500+"}),
        ("Unknown", {"position": 9, "label": 'Unknown'}),
        (1000000, None)
    ],
    "gender_distribution": [
        ("All genders", {"position": 1, "label": "All genders"}),
        ("Female", {"position": 2, "label": "Female"}),
        ("Male", {"position": 3, "label": "Male"}),
        ("Transgender", {"position": 4, "label": "Transgender"}),
        ("Other", {"position": 5, "label": "Other"}),
    ],
    "operating_for_distribution": [
        (0, {"position": 1, "label": 'Yet to start'}),
        (0.1, {"position": 2, "label": 'Less than 12 months'}),
        (1, {"position": 3, "label": 'Less than 3 years'}),
        (3, {"position": 4, "label": '4 years or more'}),
        ("Unknown", {"position": 5, "label": 'Unknown'}),
        (1000000, None)
    ],
    "age_group_distribution": [
        ("Older adults (80+)", {
            "label": "Older adults (80+)",
            "age_from": 80,
            "age_to": 150,
            "position": 1
        }),
        ("Mature adults (51-80 years)", {
            "label": "Mature adults (51-80 years)",
            "age_from": 51,
            "age_to": 80,
            "position": 2
        }),
        ("Adults (36-50 years)", {
            "label": "Adults (36-50 years)",
            "age_from": 36,
            "age_to": 50,
            "position": 3
        }),
        ("Young adults (20-35 years)", {
            "label": "Young adults (20-35 years)",
            "age_from": 20,
            "age_to": 35,
            "position": 4
        }),
        ("Adolescents (12-19 years)", {
            "label": "Adolescents (12-19 years)",
            "age_from": 12,
            "age_to": 19,
            "position": 5
        }),
        ("Children (4-11 years)", {
            "label": "Children (4-11 years)",
            "age_from": 4,
            "age_to": 11,
            "position": 6
        }),
        ("Infants (0-3 years)", {
            "label": "Infants (0-3 years)",
            "age_from": 0,
            "age_to": 3,
            "position": 7
        }),
        ("All ages", {
            "label": "All ages",
            "age_from": 0,
            "age_to": 150,
            "position": 8
        })
    ],
    "beneficiary_distribution": [(b, {
        "label": ben_categories[b]["label"],
        "group": ben_categories[b]["position"],
        "sort": b,
        "position": ben_categories[b]["position"],
    }) for b in ben_categories],
    "geographic_scale_distribution": [
        (2, {"position": 1, "label": "An entire country"}),
        (0, {"position": 2, "label": "One or more local areas"}),
        (1, {"position": 3, "label": "One or more regions"}),
        (3, {"position": 4, "label": "Across many countries"})
    ],
    "country_distribution": [
        (c["alpha2"], {"name": c["name"], "alpha2": c["alpha2"]})
        for c in get_countries(os.path.join(os.path.dirname(__file__), '..', 'countries.csv'))
    ]
}
DISTRIBUTIONS["volunteers_distribution"] = DISTRIBUTIONS["employees_distribution"]

AMOUNT_STEP = 5000


def fund_summary_query(fund_slug, one_year_before):
    return [
        {
            "$match": {
                "fund_slug": fund_slug,
                "awardDate": {"$gt": one_year_before}
            }
        }, {
            "$facet": {

                # basic aggregation
                "aggregates": [{
                    "$group": {
                        "_id": "$fund_slug",
                        "period_end": {"$max": "$awardDate"},
                        "period_start": {"$min": "$awardDate"},
                        "grant_count": {"$sum": 1},
                        "recipient_count": {"$sum": 1},
                        "amount_awarded_sum": {"$sum": "$amountAwarded"},
                        "amount_awarded_mean": {"$avg": "$amountAwarded"},
                        "amount_awarded_median": {"$avg": "$amountAwarded"},  # @TODO: currently doesn't work
                        "amount_awarded_min": {"$min": "$amountAwarded"},
                        "amount_awarded_max": {"$max": "$amountAwarded"},
                        "duration_awarded_months_mean": {"$avg": {"$arrayElemAt": ["$plannedDates.duration", 0]}},
                        "duration_awarded_months_median": {"$avg": {"$arrayElemAt": ["$plannedDates.duration", 0]}},  # @TODO: currently doesn't work
                        "duration_awarded_months_min": {"$min": {"$arrayElemAt": ["$plannedDates.duration", 0]}},
                        "duration_awarded_months_max": {"$max": {"$arrayElemAt": ["$plannedDates.duration", 0]}},
                    }
                }],

                # source and license
                "source_license": [{
                    "$group": {
                        "_id": {"license": "$dataset.license", "source": "$dataset.source"},
                        "grant_count": {"$sum": 1}
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "license": "$_id.license",
                        "source": "$_id.source"
                    }
                }],

                # # @TODO: change to bucket into similar groups to income
                # "amount_awarded_distribution": [{
                #     "$bucket": {
                #           "groupBy": "$amountAwarded",
                #           "boundaries": [ 0, 10000, 100000, 1000000, 10000000, 1000000000 ],
                #           "default": "Unknown",
                #           "output": {
                #             "count": { "$sum": 1 },
                #             "sum": {"$sum": "$amountAwarded" },
                #           }
                #     }
                # }],

                # Distribution of awarded amounts, in bands of 5000
                "amount_awarded_distribution": [{
                    "$group": {
                        "_id": {"$multiply": [{"$floor": {"$divide": ["$amountAwarded", AMOUNT_STEP]}}, AMOUNT_STEP]},
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }, {
                    "$sort": {"_id": 1}
                }],

                # Distribution by duration of grants
                "duration_awarded_months_distribution": [{
                    "$bucket": {
                        "groupBy": {"$arrayElemAt": ["$plannedDates.duration", 0]},
                        "boundaries": [0, 3, 6, 12, 18, 24, 36, 48, 1000],
                        "default": "Missing",
                        "output": {
                            "count": {"$sum": 1},
                            "sum": {"$sum": "$amountAwarded"},
                        }
                    }
                }],

                # Distribution by month awarded
                "award_month_distribution": [{
                    "$group": {
                        "_id": {"$month": "$awardDate"},
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }, {
                    "$sort": {"_id": 1}
                }, {
                    "$project": {
                        "_id": 0,
                        "month": "$_id",
                        "count": "$count",
                        "sum": "$sum",
                    }
                }],

                # Distribution by organisation type
                "org_type_distribution": [{
                    "$group": {
                        "_id": "$beehive.org_type",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # Distribution by recipient income
                "income_distribution": [{
                    "$bucket": {
                        "groupBy": "$beehive.income",
                        "boundaries": [0, 10000, 100000, 1000000, 10000000, 1000000000],
                        "default": "Unknown",
                        "output": {
                            "count": {"$sum": 1},
                            "sum": {"$sum": "$amountAwarded"},
                        }
                    }
                }],

                # Distribution by recipient employees
                "employees_distribution": [{
                    "$bucket": {
                        "groupBy": "$beehive.employees",
                        "boundaries": [0, 1, 5, 25, 50, 100, 250, 500, 1000000],
                        "default": "Unknown",
                        "output": {
                            "count": {"$sum": 1},
                            "sum": {"$sum": "$amountAwarded"},
                        }
                    }
                }],

                # Distribution by recipient volunteers
                "volunteers_distribution": [{
                    "$bucket": {
                        "groupBy": "$beehive.volunteers",
                        "boundaries": [0, 1, 5, 25, 50, 100, 250, 500, 1000000],
                        "default": "Unknown",
                        "output": {
                            "count": {"$sum": 1},
                            "sum": {"$sum": "$amountAwarded"},
                        }
                    }
                }],

                # Distribution by how long recipient has been operating
                "operating_for_distribution": [{
                    "$bucket": {
                        "groupBy": "$beehive.operating_for",
                        "boundaries": [0, 0.1, 1, 3, 1000000],
                        "default": "Unknown",
                        "output": {
                            "count": {"$sum": 1},
                            "sum": {"$sum": "$amountAwarded"},
                        }
                    }
                }],

                # Distribution by beneficiary gender
                "gender_distribution": [{
                    "$group": {
                        "_id": "$beehive.gender",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # Distribution by beneficiary age
                "age_group_distribution": [{
                    "$unwind": "$beehive.ages"
                }, {
                    "$group": {
                        "_id": "$beehive.ages.label",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # Distribution by beneficiary groups
                "beneficiary_distribution": [{
                    "$unwind": "$beehive.beneficiaries"
                }, {
                    "$group": {
                        "_id": "$beehive.beneficiaries",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # Distribution by beneficiary geography
                "geographic_scale_distribution": [{
                    "$group": {
                        "_id": "$beehive.geographic_scale",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # Distribution by beneficiary country
                "country_distribution": [{
                    "$unwind": "$beehive.countries"
                }, {
                    "$group": {
                        "_id": "$beehive.countries",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # Distribution by beneficiary location (district)
                "district_distribution": [{
                    "$unwind": "$beehive.districts"
                }, {
                    "$group": {
                        "_id": "$beehive.districts",
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$amountAwarded"},
                    }
                }],

                # examples of grants
                "grant_examples": [{
                    "$sample": {"size": 3}
                }, {
                    "$project": {
                        "_id": 0,
                        "title": "$title",
                        "recipient": {"$arrayElemAt": ["$recipientOrganization.name", 0]},
                        "amount": "$amountAwarded",
                        "currency": "$currency",
                        "award_date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$awardDate"}},
                        "id": "$_id",
                    }
                }]
            }
        }, {
            "$project": {
                "sources": "$source_license",
                "fund_slug": {"$arrayElemAt": ["$aggregates._id", 0]},
                "period_end": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$arrayElemAt": ["$aggregates.period_end", 0]}}},
                "period_start": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$arrayElemAt": ["$aggregates.period_start", 0]}}},
                "grant_count": {"$arrayElemAt": ["$aggregates.grant_count", 0]},
                "recipient_count": {"$arrayElemAt": ["$aggregates.recipient_count", 0]},
                "amount_awarded_sum": {"$arrayElemAt": ["$aggregates.amount_awarded_sum", 0]},
                "amount_awarded_mean": {"$arrayElemAt": ["$aggregates.amount_awarded_mean", 0]},
                "amount_awarded_median": {"$arrayElemAt": ["$aggregates.amount_awarded_median", 0]},
                "amount_awarded_min": {"$arrayElemAt": ["$aggregates.amount_awarded_min", 0]},
                "amount_awarded_max": {"$arrayElemAt": ["$aggregates.amount_awarded_max", 0]},
                "amount_awarded_distribution": "$amount_awarded_distribution",
                "duration_awarded_months_mean": {"$arrayElemAt": ["$aggregates.duration_awarded_months_mean", 0]},
                "duration_awarded_months_median": {"$arrayElemAt": ["$aggregates.duration_awarded_months_median", 0]},
                "duration_awarded_months_min": {"$arrayElemAt": ["$aggregates.duration_awarded_months_min", 0]},
                "duration_awarded_months_max": {"$arrayElemAt": ["$aggregates.duration_awarded_months_max", 0]},
                "duration_awarded_months_distribution": "$duration_awarded_months_distribution",
                "award_month_distribution": "$award_month_distribution",
                "org_type_distribution": "$org_type_distribution",
                "operating_for_distribution": "$operating_for_distribution",
                "income_distribution": "$income_distribution",
                "employees_distribution": "$employees_distribution",
                "volunteers_distribution": "$volunteers_distribution",
                "gender_distribution": "$gender_distribution",
                "age_group_distribution": "$age_group_distribution",
                "beneficiary_distribution": "$beneficiary_distribution",
                "geographic_scale_distribution": "$geographic_scale_distribution",
                "country_distribution": "$country_distribution",
                "district_distribution": "$district_distribution",
                "grant_examples": "$grant_examples",
            }
        }
    ]


def process_fund_summary(results):

    # process distributions
    distributions = [
        "amount_awarded_distribution",
        "duration_awarded_months_distribution",
        "award_month_distribution",
        "org_type_distribution",
        "operating_for_distribution",
        "income_distribution",
        "employees_distribution",
        "volunteers_distribution",
        "gender_distribution",
        "age_group_distribution",
        "beneficiary_distribution",
        "geographic_scale_distribution",
        "country_distribution",
        "district_distribution",
    ]
    for d in distributions:
        if d in DISTRIBUTIONS:
            new_d = []
            for i in DISTRIBUTIONS[d]:
                if not i[1]:
                    continue
                new_i = i[1]
                new_i["count"] = 0
                new_i["sum"] = 0
                for r in results[d]:
                    if r["_id"] == i[0]:
                        new_i["count"] = r["count"]
                        new_i["sum"] = r["sum"]
                new_d.append(new_i)
            results[d] = new_d
        results[d] = process_distribution(results[d], d, results["grant_count"])

    results["sources"] = {s["license"]: s.get("source") for s in results.get("sources", {})}
    return results


def process_distribution(distribution, dist_name, total=None):

    # actions for particular distributions
    if dist_name == "amount_awarded_distribution":
        distribution = [{
            "segment": i["_id"] / AMOUNT_STEP,
            "start": i["_id"],
            "end": i["_id"] + (AMOUNT_STEP - 1),
            "count": i["count"],
            "sum": i["sum"]
        } for i in distribution]

    elif dist_name == "country_distribution":
        distribution = [i for i in distribution if i["count"] > 0]

    if not total:
        total = sum([a["count"] for a in distribution])
    return [add_percent(a, total) for a in distribution]


def add_percent(row, total):
    row["percent"] = float(row["count"]) / total
    return row
