from imdb import IMDb

ia = IMDb()

for person in ia.search_person('Mel Gibson'):
    print(person.personID, person['name'])

top250 = ia.get_top250_movies()
bottom100 = ia.get_bottom100_movies()

for movie in top250[0:10]:
    print movie

for movie in bottom100[-10:]:
    print movie
