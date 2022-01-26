import pytest

from wikipedia_ql import media_wiki

@pytest.fixture
def wiki():
    return media_wiki.Wikipedia(cache_folder='tests/_cache')

def test_rotten_tomatoes(wiki):
    assert wiki.query(r'''
        from "Nomadland (film)" {
            section[heading="Critical response"] >> {
                sentence:contains("Rotten Tomatoes") >> {
                    text:matches("\d+%") as "percent";
                    text:matches("(\d+) (critic|reviews)") >> text-group[group=1] as "reviews";
                    text:matches("[\d.]+/10") as "overall"
                }
            }
        }
    ''') == [{'overall': '8.80/10', 'percent': '94%', 'reviews': '417'}]

def test_attributes(wiki):
    assert wiki.query(r'''
        from "Bear" {
            section[heading="Feeding"] >> img@src as "image";
            section[heading="Phylogeny"] >> sentence:contains("clade") >> a@href
        }
    ''') == [
        {'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Giant_Panda_Tai_Shan.JPG/220px-Giant_Panda_Tai_Shan.JPG'},
        {'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bear_Alaska_%283%29.jpg/220px-Bear_Alaska_%283%29.jpg'},
        {'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Polar_bear_%28Ursus_maritimus%29_with_its_prey.jpg/220px-Polar_bear_%28Ursus_maritimus%29_with_its_prey.jpg'},
        'https://en.wikipedia.org/wiki/Clade'
    ]

    # Standalone attr & standalone text
    assert wiki.query(r'''
        from "Björk" {
            section[heading="Discography"] >> {
                li >> a >> {
                    text as "title";
                    @href as "link"
                }
            }
        }
    ''') == [
        {'link': 'https://en.wikipedia.org/wiki/Debut_(Björk_album)', 'title': 'Debut'},
        {'link': 'https://en.wikipedia.org/wiki/Post_(Björk_album)', 'title': 'Post'},
        {'link': 'https://en.wikipedia.org/wiki/Homogenic', 'title': 'Homogenic'},
        {'link': 'https://en.wikipedia.org/wiki/Vespertine', 'title': 'Vespertine'},
        {'link': 'https://en.wikipedia.org/wiki/Medúlla', 'title': 'Medúlla'},
        {'link': 'https://en.wikipedia.org/wiki/Volta_(album)', 'title': 'Volta'},
        {'link': 'https://en.wikipedia.org/wiki/Biophilia_(album)', 'title': 'Biophilia'},
        {'link': 'https://en.wikipedia.org/wiki/Vulnicura', 'title': 'Vulnicura'},
        {'link': 'https://en.wikipedia.org/wiki/Utopia_(Björk_album)', 'title': 'Utopia'}
    ]

def test_category(wiki):
    assert wiki.query('''
        from category:"2020s American time travel television series" {
            page@title as "title";
            section[heading="External links"] >> {
              li >> text:matches("^(.+?) at IMDb") >> text-group[group=1] >> a@href as "imdb"
            }
        }
    ''') == [
        {'imdb': 'https://www.imdb.com/title/tt2364582/',
         'title': 'Agents of S.H.I.E.L.D.'},
        {'imdb': 'https://www.imdb.com/title/tt3107288/',
         'title': 'The Flash (2014 TV series)'},
        {'imdb': 'https://www.imdb.com/title/tt4532368/',
         'title': 'Legends of Tomorrow'},
        {'imdb': 'https://www.imdb.com/title/tt9140554/',
         'title': 'Loki (TV series)'},
        {'imdb': 'https://www.imdb.com/title/tt3006802/',
         'title': 'Outlander (TV series)'},
        {'imdb': 'https://www.imdb.com/title/tt10329642/',
         'title': 'Secrets of Sulphur Springs'},
        {'imdb': 'https://www.imdb.com/title/tt1312171/',
         'title': 'The Umbrella Academy (TV series)'},
    ]

def test_follow_links(wiki):
    assert wiki.query(r'''
        from "Björk" {
            section[heading="Discography"] >> {
                li >> a -> {
                    page@title as "title";
                    .infobox-image:first-of-type >> img@src as "cover"
                }
            }
        }
    ''') == [
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/7/77/Bj%C3%B6rk-Debut-1993.png/220px-Bj%C3%B6rk-Debut-1993.png',
         'title': 'Debut (Björk album)'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/3/3f/Bjork_Post.png/220px-Bjork_Post.png',
         'title': 'Post (Björk album)'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/af/Bj%C3%B6rk_-_Homogenic.png/220px-Bj%C3%B6rk_-_Homogenic.png',
         'title': 'Homogenic'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/1/14/Bj%C3%B6rk_-_Vespertine_album_cover.png/220px-Bj%C3%B6rk_-_Vespertine_album_cover.png',
         'title': 'Vespertine'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/6/6d/Medulla.png/220px-Medulla.png',
         'title': 'Medúlla'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e7/Bj%C3%B6rk-Volta-Latin-American-Edition.jpg/220px-Bj%C3%B6rk-Volta-Latin-American-Edition.jpg',
         'title': 'Volta (album)'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/6/6e/Biophilia_app_opening_screen.png/220px-Biophilia_app_opening_screen.png',
         'title': 'Biophilia (album)'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/ab/Vulnicura_%28deluxe_cd%29.png/220px-Vulnicura_%28deluxe_cd%29.png',
         'title': 'Vulnicura'},
        {'cover': 'https://upload.wikimedia.org/wikipedia/en/thumb/2/2c/Bj%C3%B6rk_-_Utopia_album_cover.png/220px-Bj%C3%B6rk_-_Utopia_album_cover.png',
         'title': 'Utopia (Björk album)'},
    ]

    # Drop external links to IMDB and AllMovie, only fetch internal ones
    assert wiki.query(r'''
        from "Wander Darkly" {
            section[heading="External links"] -> { page@title }
        }
    ''') == ['IMDb', 'AllMovie']

def test_table_filmography(wiki):
    # assert wiki.query(r'''
    #     from "Kharkiv" {
    #         section[heading="Climate"] >> table >> table-data {
    #             tr[title="Average low °C (°F)"] >> td {
    #                 @column as "month";
    #                 text as "temp"
    #             }
    #         }
    #     }
    # ''') == [
    # ]

    assert wiki.query(r'''
        from "The Wachowskis" {
            section[heading="Films"] >> table >> table-data >> tr >> {
                td[column$="directors"] as "directors";
                td[column="Year"] as "year";
                td[column="Title"] >> a -> {
                    @title as "film";
                    section[heading="Critical response"]
                        >> sentence:contains("Rotten Tomatoes")
                        >> text:matches("\d+%") as "rotten-tomatoes";
                }
            }
        }
    ''') == [
        {'film': 'Assassins (1995 film)', 'year': '1995'},
        {'film': 'Bound (1996 film)', 'rotten-tomatoes': '89%', 'year': '1996'},
        {'film': 'The Matrix', 'rotten-tomatoes': '88%', 'year': '1999'},
        {'film': 'The Matrix Revisited', 'year': '2001'},
        {'film': 'The Animatrix', 'year': '2003'},
        {'film': 'The Matrix Reloaded', 'rotten-tomatoes': '73%', 'year': '2003'},
        {'film': 'The Matrix Revolutions', 'rotten-tomatoes': '35%', 'year': '2003'},
        {'film': 'V for Vendetta (film)', 'rotten-tomatoes': '73%', 'year': '2005'},
        {'film': 'The Invasion (film)', 'year': '2007'},
        {'film': 'Speed Racer (film)', 'rotten-tomatoes': '41%', 'year': '2008'},
        {'film': 'Ninja Assassin', 'rotten-tomatoes': '26%', 'year': '2009'},
        {'film': 'Cloud Atlas (film)', 'rotten-tomatoes': '66%', 'year': '2012'},
        # FIXME: What's this?..
        {'year': '2014'},
        {'film': 'Jupiter Ascending', 'rotten-tomatoes': '28%', 'year': '2015'},
        {'film': 'The Matrix Resurrections', 'rotten-tomatoes': '62%', 'year': '2021'},
        {},
    ]
