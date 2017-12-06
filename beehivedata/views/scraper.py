from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from werkzeug.contrib.atom import AtomFeed

import base64

from ..db import get_db

scraper = Blueprint('scraper', __name__)


@scraper.route('/notifications')
@login_required
def notifications():
    db = get_db()
    notifications = db.notifications.find(
        {}, sort=[("date_issued", -1)], limit=100)
    return render_template('notifications.html', notifications=list(notifications))


@scraper.route('/notifications.atom')
def notifications_feed():
    feed = AtomFeed('Recently updated funds',
                    feed_url=request.url,
                    url=request.url_root,
                    author="Beehive")
    db = get_db()
    notifications = db.notifications.find({}, sort=[("date_issued", -1)], limit=100)
    for article in notifications:
        feed.add(article["notice"], article.get("content", ""),
                 id=str(article["_id"]),
                 url=article["fund"],
                 updated=article["date_issued"],
                 published=article["date_issued"],
                 content_type='text',
        )
    return feed.get_response()


@scraper.route('/funds')
@login_required
def scraper_funds():
    db = get_db()
    funds = db.scraped_funds.aggregate([
        { "$group": {"_id": "$funder", "funds": {"$push": "$$ROOT"}}}
    ])
    return render_template('scrapes.html', funders=list(funds))


@scraper.route('/funds/<fund_id>')
@login_required
def scraper_fund(fund_id):
    fund_id = base64.urlsafe_b64decode(fund_id).decode('utf8')
    db = get_db()
    funds = db.scraped_funds.find({"_id": fund_id})
    return render_template('scrape.html', scrapes=list(funds))


@scraper.route('/scrape/<scrapeid>')
@login_required
def scraper_scrape(scrapeid):
    db = get_db()
    funds = db.scraped_funds.find({"scrapes.contentHash": scrapeid})
    return render_template('scrape.html', scrapes=list(funds))
