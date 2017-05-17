from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *
import argparse
import csv
import os
import urllib.request
from dateutil.parser import parse

THREE_SIXTY_MAPPING = {
    "grant": [
        ('Identifier', 'grant_identifier', None),
        ('Title', 'title', None),
        ('Description', 'description', None),
        ('Currency', 'currency', 'GBP'),
        ('Grant Programme:Title', 'funding_programme', None),
        ('Amount Awarded', 'amount_awarded', None),
        ('Amount Applied For', 'amount_applied_for', None),
        ('Amount Disbursed', 'amount_disbursed', None),
        ('Award Date', 'award_date', None),
        ('Planned Dates:Start Date', 'planned_start_date', None),
        ('Planned Dates:End Date', 'planned_end_date', None),
        ('Planned Dates:Duration (months)', 'duration_funded_months', 12),
        ('From an open call?', 'open_call', None),
    ],
    "recipient": [
        ('Recipient Org:Identifier', 'organisation_identifier', None),
        ('Recipient Org:Name', 'name', None),
        ('Recipient Org:Company Number', 'company_number', None),
        ('Recipient Org:Charity Number', 'charity_number', None),
        ('Recipient Org:Street Address', 'street_address', None),
        ('Recipient Org:City', 'city', None),
        ('Recipient Org:County', 'region', None),
        ('Recipient Org:Country', 'country', 'GB'),
        ('Recipient Org:Postal Code', 'postal_code', None),
        ('Recipient Org:Web Address', 'website', None),
    ],
    "funder": [
        ('Funding Org:Identifier', 'organisation_identifier', None),
        ('Funding Org:Name', 'name', None),
    ]
}

date_fields = ['award_date', 'planned_start_date', 'planned_end_date']
number_fields = ['amount_awarded', 'amount_applied_for', 'amount_disbursed']

        # ('Classifications:Title', ''),
        # ('Beneficiary Location:0:Geographic Code Type', ''),
        # ('Beneficiary Location:0:Geographic Code', ''),
        # ('Beneficiary Location:0:Name', ''),
        # ('Beneficiary Location:1:Geographic Code Type', ''),
        # ('Beneficiary Location:1:Geographic Code', ''),
        # ('Beneficiary Location:1:Name', ''),
        # ('Recipient Org:Description', ''),
        # ('Grant Programme:Code', ''),
        # ('Grant Programme:URL', ''),
        # ('Last Modified Date', ''),

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        # session.add(instance)
        # session.commit()
        return instance

def main():

    parser = argparse.ArgumentParser(description='Process 360 giving standard CSV to database')
    parser.add_argument('input', help='Location of CSV or JSON file (URL or file)')
    parser.add_argument('--csv', dest='filetype', action='store_const', const='csv', help='Specifies a CSV file')
    parser.add_argument('--json', dest='filetype', action='store_const', const='json', help='Specifies a JSON file')
    parser.add_argument('--db', default='postgres://postgres:postgres@localhost/beehive-data_development', help='Database URL to connect to')
    parser.add_argument('--encoding', default='utf8', help='Encoding of CSV file')
    parser.set_defaults(filetype='csv')
    args = parser.parse_args()

    engine = create_engine(args.db)
    Session = sessionmaker(bind=engine)
    session = Session()
    #
    # g = session.query(Grant).first()
    # print(g)


    if os.path.isfile(args.input):
        filename = args.input
        print("Using existing file: %s" % args.input)
    else:
        filename = "data/%s" % args.input.split('/')[-1]
        print("Downloading from: %s" % args.input)
        urllib.request.urlretrieve(args.input, filename)
        print("Saved as: %s" % filename)

    if args.filetype=='csv':
        # open the CSV file
        with open(filename, encoding=args.encoding) as a:
            reader = csv.DictReader(a)
            for row in reader:
                # check for malformed/empty row
                if len([f for f in row if row[f]!=''])==0:
                    continue

                row_data = {}
                for t in THREE_SIXTY_MAPPING:
                    d = {}
                    for f in THREE_SIXTY_MAPPING[t]:
                        # get the value from CSV
                        d[f[1]] = row.get(f[0], f[2])

                        # check for blank text
                        if d[f[1]]=='':
                            d[f[1]] = None

                        # convert number fields
                        if f[1] in number_fields and d[f[1]]:
                            d[f[1]] = float(d[f[1]])

                        # convert date fields
                        if f[1] in date_fields and d[f[1]]:
                            d[f[1]] = parse(d[f[1]], dayfirst=True, ignoretz=True)

                    row_data[t] = d

                # get the recipient's country
                if row_data["recipient"]["country"] == 'UK':
                    row_data["recipient"]["country"] = 'GB'
                row_data["recipient"]["country"] = session.query(Country).filter_by(alpha2=row_data["recipient"]["country"]).first()

                # find the recipient or create a new one
                recipient = get_or_create(session, Organisation,
                                          organisation_identifier= row_data["recipient"]["organisation_identifier"])
                recipient.update(row_data["recipient"])
                session.add(recipient)

                # find the funder or create a new one
                funder = get_or_create(session, Funder,
                                       organisation_identifier= row_data["funder"]["organisation_identifier"])
                funder.update(row_data["funder"])
                session.add(funder)

                # find the grant or create a new one
                grant = get_or_create(session, Grant, grant_identifier=row_data["grant"]["grant_identifier"])

                # sort out grant data
                grant_data = row_data["grant"]
                grant_data["recipient"] = recipient
                grant_data["funder"] = funder

                grant.update(row_data["grant"])
                grant.award_year = grant.award_date.year if grant.award_date else None

                session.add(grant)
                session.commit()
                print(recipient)
                print(funder)
                print(grant)
                pass

if __name__ == '__main__':
    main()
