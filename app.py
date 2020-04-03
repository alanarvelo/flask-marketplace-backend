#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
import operator

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

# TODO: connect to a local postgresql database
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

###########################  SHOWS  ######################
class Show(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))
  artist = db.relationship("Artist", back_populates="venues")
  venue = db.relationship("Venue", back_populates="artists")

  venue_name = db.Column(db.String, nullable=False)
  artist_name = db.Column(db.String, nullable=False)
  artist_image_link = db.Column(db.String(500))
  start_time = db.Column(db.DateTime)

  def __repr__(self):
      return f'<Show: {self.id}, Venue: ({self.venue_id}, {self.venue_name}), Artist: ({self.artist_id}, {self.artist_name})>'

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String(50)), default=dict)
    website = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    artists = db.relationship('Show', back_populates="venue")

    def __repr__(self):
      return f'<Venue: {self.id}, {self.name}, {self.city}>'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String(50)), default=dict)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    venues = db.relationship('Show', back_populates="artist")

    def __repr__(self):
      return f'<Artist: {self.id}, {self.name}>'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

####### VENUES #######

def show_count_per_venue(venue_id, upcoming=True):
  try:
    if upcoming:
      comp = operator.ge
    else:
      comp = operator.lt
    return  db.session.query(db.func.count(Show.start_time))\
                .filter(Venue.id == venue_id, Venue.id == Show.venue_id, comp(Show.start_time, datetime.now()))\
                .first()[0]
  except:
    print(sys.exc_info())

def show_list_per_venue(venue_id, upcoming=True):
  try:
    if upcoming:
      comp = operator.ge
    else:
      comp = operator.lt
    shows = db.session.query(Show.artist_id, Show.artist_name, Show.artist_image_link, \
                db.func.cast(Show.start_time, db.String).label("start_time"))\
                .filter(Venue.id == venue_id, Venue.id == Show.venue_id, comp(Show.start_time, datetime.now()))\
                .all()
    shows = [s._asdict() for s in shows]
    return shows
  except:
    print(sys.exc_info())


####### ARTISTS #######

def show_count_per_artist(artist_id, upcoming=True):
  try:
    if upcoming:
      comp = operator.ge
    else:
      comp = operator.lt
    return  db.session.query(db.func.count(Show.start_time))\
                .filter(Artist.id == artist_id, Artist.id == Show.artist_id, comp(Show.start_time, datetime.now()))\
                .first()[0]
  except:
    print(sys.exc_info())

def show_list_per_artist(artist_id, upcoming=True):
  try:
    if upcoming:
      comp = operator.ge
    else:
      comp = operator.lt
    shows = db.session.query(Show.venue_id, Show.venue_name, Venue.image_link.label("venue_image_link"), \
                db.func.cast(Show.start_time, db.String).label("start_time"))\
                .filter(Artist.id == artist_id, \
                        Artist.id == Show.artist_id, \
                        Venue.id == Show.venue_id, \
                        comp(Show.start_time, datetime.now()))\
                .all()
    shows = [s._asdict() for s in shows]
    return shows
  except:
    print(sys.exc_info())



#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  try: 
    data = db.session.query(Venue.city, Venue.state).distinct().all()
    data = [{**d._asdict(), 'venues': []} for d in data]
    for city in data:
      venues_in_city = db.session.query(Venue.id, Venue.name).filter(Venue.city == city["city"]).all()
      venues_in_city = [{**v._asdict(), 'num_upcoming_shows': show_count_per_venue(v.id)} for v in venues_in_city]
      city["venues"] = venues_in_city
      
    print("/venues : {}".format(data))
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  try:
    search_term = request.form.get('search_term', '')
    venues = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike(f'%{search_term}%')).all()
    venues = [x._asdict() for x in venues]
    for v in venues:
      v["num_upcoming_shows"] = show_count_per_venue(v['id'], upcoming=True)
    response = {
      "count": len(venues),
      "data": venues
    }
    print("######## /venues/search : {}".format(response))
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try: 
    data = Venue.query.get(venue_id).__dict__
    del data["_sa_instance_state"]

    data["upcoming_shows_count"] = show_count_per_venue(venue_id, upcoming=True)
    data["past_shows_count"] = show_count_per_venue(venue_id, upcoming=False)
    
    data["upcoming_shows"] = []
    if data["upcoming_shows_count"]:
      data["upcoming_shows"] = show_list_per_venue(venue_id, upcoming=True)
    
    data["past_shows"] = []
    if data["past_shows_count"]:
      data["past_shows"] = show_list_per_venue(venue_id, upcoming=False)

    print(data)
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  body = {}
  try: 
    data = dict(request.form)
    if "genres" in data:
      data["genres"] = request.form.getlist("genres")
    venue = Venue(**data)
    db.session.add(venue)
    db.session.commit()
    print("########## /venues/create : {}".format(data))
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + data["name"] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Venue ' + data["name"] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  body = {}
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    print("########## /venues/id/delete : {}".format(venue))
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred while deleting.')
    else:
      # on successful db insert, flash success
      flash('Deletion successful')
    return render_template('pages/home.html')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  try: 
    artists = db.session.query(Artist.id, Artist.name).all()
    artists = [a._asdict() for a in artists]
    print("/artists : {}".format(artists))
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  try:
    search_term = request.form.get('search_term', '')
    artists = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike(f'%{search_term}%')).all()
    artists = [x._asdict() for x in artists]
    for a in artists:
      a["num_upcoming_shows"] = show_count_per_artist(a['id'], upcoming=True)
    response = {
      "count": len(artists),
      "data": artists
    }
    print("######## /venues/search : {}".format(response))
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try: 
    artist = Artist.query.get(artist_id).__dict__
    del artist["_sa_instance_state"]

    artist["upcoming_shows_count"] = show_count_per_artist(artist_id, upcoming=True)
    artist["past_shows_count"] = show_count_per_artist(artist_id, upcoming=False)
    
    artist["upcoming_shows"] = []
    if artist["upcoming_shows_count"]:
      artist["upcoming_shows"] = show_list_per_artist(artist_id, upcoming=True)
    
    artist["past_shows"] = []
    if artist["past_shows_count"]:
      artist["past_shows"] = show_list_per_artist(artist_id, upcoming=False)

    print("/artists/id : {}".format(artist))
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id).__dict__
  del artist["_sa_instance_state"]
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try: 
    artist = Artist.query.get(artist_id)
    data = dict(request.form)
    if "genres" in data:
      data["genres"] = request.form.getlist("genres")

    for key, value in data.items():
      if value:
        setattr(artist, key, value)

    db.session.commit()
    print("########### /artists/id/edit : {}".format(artist))
  except:
    print(sys.exc_info())
  finally:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id).__dict__
  del venue["_sa_instance_state"]
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try: 
    venue = Venue.query.get(venue_id)
    data = dict(request.form)
    if "genres" in data:
      data["genres"] = request.form.getlist("genres")

    for key, value in data.items():
      if value:
        setattr(venue, key, value)

    db.session.commit()
    print("########### /venues/id/edit : {}".format(venue))
  except:
    print(sys.exc_info())
  finally:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  body = {}
  try: 
    data = dict(request.form)
    if "genres" in data:
      data["genres"] = request.form.getlist("genres")
    artist = Artist(**data)
    db.session.add(artist)
    db.session.commit()
    print("########## /artists/create : {}".format(data))
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + data["name"] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Artist ' + data["name"] + ' was successfully listed!')
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real shows data.
  try: 
    shows = db.session.query(Show.venue_id, Show.venue_name, Show.artist_id, Show.artist_name, Show.artist_image_link, 
                db.func.cast(Show.start_time, db.String).label("start_time"))\
                .all()
    shows = [a._asdict() for a in shows]
    print("/shows : {}".format(shows))
  except:
    print(sys.exc_info())
  finally:
    return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  body = {}
  try: 
    data = dict(request.form)
    if not data["venue_id"] or not data["artist_id"]:
      raise Exception
    data["venue_id"] = int(data["venue_id"])
    data["artist_id"] = int(data["artist_id"])
    compl_data = db.session.query(Venue.name.label("venue_name"), Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"))\
                      .filter(Venue.id == data["venue_id"], Artist.id == data["artist_id"]).first()
    if not compl_data:
      raise Exception
    data.update(compl_data._asdict())
    show = Show(**data)
    db.session.add(show)
    db.session.commit()
    print("########## /shows/create : {}".format(data))
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Show could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    return render_template('pages/home.html')



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
