from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table, DateTime, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, backref
import datetime

Base = declarative_base()

class updateMixin(object):
    def update(self, values):
        for key,value in values.items():
            setattr(self, key, value)


ages = Table('ages',
    Base.metadata,
    Column('age_group_id', Integer, ForeignKey('age_groups.id')),
    Column('grant_id', Integer, ForeignKey('grants.id'))
)

locations = Table('locations',
    Base.metadata,
    Column('country_id', Integer, ForeignKey('countries.id')),
    Column('grant_id', Integer, ForeignKey('grants.id'))
)

regions = Table('regions',
    Base.metadata,
    Column('district_id', Integer, ForeignKey('districts.id')),
    Column('grant_id', Integer, ForeignKey('grants.id'))
)

stakeholders = Table('stakeholders',
    Base.metadata,
    Column('beneficiary_id', Integer, ForeignKey('beneficiaries.id')),
    Column('grant_id', Integer, ForeignKey('grants.id')),
    Column('created_at', DateTime, default=datetime.datetime.now),
    Column('updated_at', DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
)

class Grant(Base, updateMixin):
    __tablename__ = 'grants'

    id = Column(Integer, primary_key=True)
    funder_id = Column(Integer, ForeignKey('organisations.id'))
    recipient_id = Column(Integer, ForeignKey('organisations.id'))
    grant_identifier = Column(Text, index=True)
    title = Column(Text)
    description = Column(Text)
    currency = Column(String(3))
    funding_programme = Column(Text)
    gender = Column(Text)
    state = Column(Text, default="import")
    amount_awarded = Column(Float)
    amount_applied_for = Column(Float)
    amount_disbursed = Column(Float)
    award_date = Column(DateTime)
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    open_call = Column(Boolean)
    affect_people = Column(Boolean)
    affect_other = Column(Boolean)
    award_year = Column(Integer)
    operating_for = Column(Integer)
    income = Column(Integer)
    spending = Column(Integer)
    employees = Column(Integer)
    volunteers = Column(Integer)
    geographic_scale = Column(Integer)
    type_of_funding = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    fund_slug = Column(Text)
    duration_funded_months = Column(Integer)
    license = Column(Text)
    source = Column(Text)

    ages = relationship('AgeGroup', secondary=ages, backref=backref('grants', lazy='dynamic'))
    beneficiaries = relationship('Beneficiary', secondary=stakeholders, backref=backref('grants', lazy='dynamic'))
    countries = relationship('Country', secondary=locations, backref=backref('grants', lazy='dynamic'))
    districts = relationship('District', secondary=regions, backref=backref('grants', lazy='dynamic'))
    recipient = relationship('Organisation', backref='grants_received', foreign_keys=[recipient_id])
    funder = relationship('Funder', backref='grants_made', foreign_keys=[funder_id])

    def __repr__(self):
        return '<Grant {}: {}{:,.0f} from "{}" to "{}" in {}>'.format(self.id, self.currency, self.amount_awarded, self.funder.name, self.recipient.name, self.award_year)

    def to_json(self):
        return {
            "publisher": self.funder.name,
            "license": self.license,
            "grant_identifier": self.grant_identifier,
            "funder_identifier": self.funder.organisation_identifier,
            "funder": self.funder.name,
            "fund": self.funding_programme,
            "award_year": self.award_year,
            "title": self.title,
            "description": self.description,
            "open_call": self.open_call,
            "approval_date": self.award_date
        }

    def clean(self):

        # fill in duration if not present
        if self.planned_end_date and self.planned_start_date:
            pass

class Organisation(Base, updateMixin):
    __tablename__ = 'organisations'

    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey('countries.id'))
    organisation_identifier = Column(Text, index=True)
    slug = Column(Text, index=True)
    charity_number = Column(Text, index=True)
    company_number = Column(Text, index=True)
    organisation_number = Column(Text, index=True)
    name = Column(Text)
    state = Column(Text, default="import")
    street_address = Column(Text)
    city = Column(Text)
    region = Column(Text)
    postal_code = Column(Text)
    website = Column(Text)
    company_type = Column(Text)
    incorporated_date = Column(DateTime)
    org_type = Column(Integer)
    publisher = Column(Boolean, default=False)
    multi_national = Column(Boolean)
    registered = Column(Boolean)
    latitude = Column(Float)
    longitude = Column(Float)
    scrape = Column(JSON, default={})
    scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    __mapper_args__ = {
        'polymorphic_on': publisher,
        'polymorphic_identity': False
    }

    def __repr__(self):
        return '<Organisation {}: {} ({:,.0f} grants received)>'.format(self.id, self.name, len(self.grants_received))

    def to_json(self):
        return {
            "organisation_identifier": self.organisation_identifier,
            "name": self.name
        }

class Funder(Organisation):

    __mapper_args__ = {
        'polymorphic_identity': True
    }

    def __repr__(self):
        return '<Funder {}: {} ({:,.0f} grants made)>'.format(self.id, self.name, len(self.grants_made))

    def to_json(self):
        return {
            "organisation_identifier": self.organisation_identifier,
            "name": self.name
        }

class Country(Base, updateMixin):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(Text, index=True)
    alpha2 = Column(Text, index=True)
    currency_code = Column(Text, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    altnames = Column(JSON)
    ccaoo = Column(Text)

    organisations = relationship('Organisation', backref='country', lazy='dynamic')
    districts = relationship('District', backref='country', lazy='dynamic')

class District(Base, updateMixin):
    __tablename__ = 'districts'

    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey('countries.id'))
    name = Column(Text, index=True)
    subdivision = Column(Text)
    region = Column(Text)
    sub_country = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class AgeGroup(Base, updateMixin):
    __tablename__ = 'age_groups'

    id = Column(Integer, primary_key=True)
    label = Column(Text, index=True)
    age_from = Column(Integer)
    age_to = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class Beneficiary(Base, updateMixin):
    __tablename__ = 'beneficiaries'

    id = Column(Integer, primary_key=True)
    label = Column(Text, index=True)
    sort = Column(Text, index=True)
    group = Column(Text, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
