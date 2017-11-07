import os
import requests
import pandas as pd
from sklearn import preprocessing
from sklearn.metrics.pairwise import pairwise_distances
import scipy.stats


class Recommender:

    BENEFICIARIES = [
        'animals', 'buildings', 'care', 'crime', 'disabilities',
        'disasters', 'education', 'environment', 'ethnic', 'exploitation',
        'food', 'housing', 'mental', 'organisation', 'organisations',
        'orientation', 'physical', 'poverty', 'public', 'refugees',
        'relationship', 'religious', 'services', 'unemployed', 'water'
    ]

    def __init__(self, db):
        self.db = db

    def get_beneficiary_group(self):
        result = self.db.grants.aggregate([{
            "$unwind": "$beehive.beneficiaries"
        }, {
            "$group": {
                "_id": {
                    "fund": {
                        "$arrayElemAt": ["$grantProgramme.slug", 0]
                    },
                    "funder": {
                        "$arrayElemAt": ["$fundingOrganization.slug", 0]
                    },
                    "beneficiary": "$beehive.beneficiaries"
                },
                "count": {"$sum": 1}
            }
        }, {
            "$project": {
                "_id": 0,
                "fund_slug": {"$concat": ["$_id.funder", "-", "$_id.fund"]},
                "beneficiary": "$_id.beneficiary",
                "count": "$count"
            }
        }, {
            "$group": {
                "_id": "$fund_slug",
                "beneficiaries": {"$push": {"beneficiary": "$beneficiary", "count": "$count"}}
            }
        }])
        new_result = []
        for i in result:
            bens = {j["beneficiary"]: j["count"] for j in i["beneficiaries"]}
            total = max([bens[j] for j in bens])
            funder_data = {c: float(bens.get(c, 0)) / total for c in self.BENEFICIARIES}
            funder_data["fund_slug"] = i["_id"]
            new_result.append(funder_data)
        return new_result

    def get_amounts(self):
        result = self.db.grants.aggregate([{
            "$group": {
                "_id": {
                    "fund": {
                        "$arrayElemAt": ["$grantProgramme.slug", 0]
                    },
                    "funder": {
                        "$arrayElemAt": ["$fundingOrganization.slug", 0]
                    }
                },
                "amounts": {"$push": "$amountAwarded"},
                "durations": {"$push": {"$arrayElemAt": ["$plannedDates.duration", 0]}}
            }
        }, {
            "$project": {
                "_id": 0,
                "fund_slug": {"$concat": ["$_id.funder", "-", "$_id.fund"]},
                "amounts": "$amounts",
                "durations": "$durations"
            }
        }])
        data = []
        for i in result:
            data.append({
                "fund_slug": i["fund_slug"],
                "amounts": [a for a in i["amounts"] if a is not None],
                "durations": [a for a in i["durations"] if a is not None]
            })
        return data

    def __generate_scores(self, field, request, tolerance, bandwidth=0.1):
        result = {}
        min_request = request - tolerance
        if min_request < 0:
            min_request = 0
        max_request = request + tolerance

        for fund in self.get_amounts():
            if len(set(fund.get(field, []))) > 1:
                d = [f for f in fund[field] if isinstance(f, int)]
                kde = scipy.stats.gaussian_kde(d, bandwidth)
                result[fund["fund_slug"]] = kde.integrate_box_1d(min_request, max_request)
            else:
                result[fund["fund_slug"]] = 0
        return result

    def check_beneficiaries(self, user_input):
        funders_data = self.get_beneficiary_group()
        funders_df = pd.DataFrame(funders_data)
        funders_df.set_index('fund_slug', inplace=True)

        parsed_user_input = [[user_input.get(c, 0) for c in funders_df.columns]]

        distances = pairwise_distances(parsed_user_input, funders_df, metric='cosine', n_jobs=1)
        return pd.Series(1 - distances[0], index=funders_df.index).sort_values(ascending=False).to_dict()

    def check_amounts(self, user_input):
        return self.__generate_scores('amounts', user_input, 10000)

    def check_durations(self, user_input):
        return self.__generate_scores('durations', user_input, 1)
