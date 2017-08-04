from flask import Blueprint, jsonify, request
from flask_login import login_required

from ..db import get_db
from ..assets.recommender import Recommender
from ..assets.beneficiaries import theme_regexes
from ..actions.update_beneficiaries import classify_grant

insight = Blueprint('insight', __name__)


@insight.route('/beneficiaries', methods=['POST'])
@login_required
def insight_beneficiaries():
    recommender = Recommender(db=get_db())
    data = request.json['data']
    result = recommender.check_beneficiaries(data)
    return jsonify(result)


@insight.route('/amounts', methods=['POST'])
@login_required
def insight_amounts():
    recommender = Recommender(db=get_db())
    data = request.json['data']['amount']
    result = recommender.check_amounts(data)
    return jsonify(result)


@insight.route('/durations', methods=['POST'])
@login_required
def insight_durations():
    recommender = Recommender(db=get_db())
    data = request.json['data']['duration']
    result = recommender.check_durations(data)
    return jsonify(result)


@insight.route('/all', methods=['POST'])
@login_required
def insight_all():
    recommender = Recommender(db=get_db())
    bens = recommender.check_beneficiaries(request.json['data'].get("beneficiaries", {}))
    amounts = recommender.check_amounts(request.json['data'].get("amount", None))
    durations = recommender.check_durations(request.json['data'].get("duration", None))
    funds = set(list(bens.keys()) + list(amounts.keys()) + list(durations.keys()))
    return jsonify({f: {
        "beneficiaries": bens.get(f, 0),
        "amounts": amounts.get(f, 0),
        "durations": durations.get(f, 0),
    } for f in funds})


@insight.route('/theme', methods=['POST'])
@login_required
def insight_theme():
    desc = request.json['data'].get("description", "")
    themes = classify_grant(desc, theme_regexes)
    return jsonify({
        "themes": themes
    })
