import cherrypy
import isbnlib as isbn
import pandas as pd
import requests
from io import StringIO
import json
import cherrypy


def get_recommendation(book_isbn, distances, ref_df,
                       allow_same_author=True, allow_more_per_author=True,
                       n_books=5, min_rating=0):
    if not (isbn.is_isbn10(book_isbn) or isbn.is_isbn13(book_isbn)):
        return json.dumps({"error": "Not valid ISBN!"})
    book_isbn_ref = ref_df.loc[ref_df['ISBN'] == book_isbn, 'ref_ISBN'].values[0]
    if not book_isbn_ref:
        return json.dumps({"error": "Not enough ratings for this books"})
    nn_df = distances.sort_values(book_isbn_ref)[[book_isbn_ref, 'title', 'author', 'rating']]
    author = nn_df['author'][0]
    title = nn_df['title'][0]
    print(author, title)
    nn_df = nn_df[nn_df['rating'] >= min_rating]
    nn_df = nn_df[1:]
    if not allow_more_per_author:
        nn_df = nn_df.drop_duplicates('author')

    if not allow_same_author:
        nn_df = nn_df[nn_df['author'] != author]

    return_dict = '{"Your Book": {"title":"' + title + '", "author":"' + author + '"},'
    recommendations = nn_df[:n_books][["title", "author", "rating"]].to_json(orient="records")
    return json.loads(return_dict + '"Recommendations":' + recommendations + '}')


distances_id = "1i1OZhqcMiwjTntjt0R2yyDsCgeZdJHci"
ref_df_id = "1XL7RyMiNrO7X8LTG-kllBK3ZXQLWrudP"

url = requests.get(f'https://drive.google.com/uc?export=download&id={distances_id}')
csv_raw = StringIO(url.text)
distances = pd.read_csv(csv_raw)
distances = distances.set_index("isbn")

url = requests.get(f'https://drive.google.com/uc?export=download&id={ref_df_id}')
csv_raw = StringIO(url.text)
ref_df = pd.read_csv(csv_raw)


class Root(object):
    @cherrypy.expose
    def index(self):
        return "Hello World!"

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def recommend(self,
                  isbn=0,
                  n_books=10,
                  min_rating=8,
                  allow_same_author="False",
                  allow_more_per_author="False"):
        recommendations = get_recommendation(isbn,
                                             distances,
                                             ref_df,
                                             allow_same_author=str(allow_same_author).lower() == "true",
                                             allow_more_per_author=str(allow_more_per_author).lower() == "true",
                                             n_books=int(n_books),
                                             min_rating=int(min_rating))
        return recommendations


if __name__ == '__main__':
    cherrypy.quickstart(Root())