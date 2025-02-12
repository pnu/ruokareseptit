# Ruokareseptit

## Sovelluksen toiminnot

Sovelluksessa käyttäjät pystyvät jakamaan ruokareseptejään. Reseptissä lukee tarvittavat ainekset ja valmistusohje.
* -[x] Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
* -[x] Käyttäjä pystyy lisäämään reseptejä ja muokkaamaan ja poistamaan niitä.
* -[ ] Käyttäjä pystyy valitsemaan reseptille yhden tai useamman luokittelun (esim. alkuruoka, intialainen, vegaaninen).
* -[x] Käyttäjä näkee ja voi selailla muiden käyttäjien julkaisemia reseptejä.
* -[x] Käyttäjä pystyy etsimään reseptejä hakusanalla.
* -[ ] Käyttäjä pystyy antamaan reseptille kommentin ja arvosanan. Reseptistä näytetään kommentit ja keskimääräinen arvosana.
* -[x] Käyttäjäsivu näyttää, montako reseptiä käyttäjä on lisännyt ja listan käyttäjän lisäämistä resepteistä.
* -[ ] Käyttäjäsivulla voi muokata omia kommentteja ja arvosteluita.

## Asennus

Kloonaa git-repositorio omaan ympäristöösi ja siirry sen
juurihakemistoon. Ota käyttöön `venv` ympäristö ja asenna
`flask`-kirjasto.

```
python3 -m venv venv
source venv/bin/activate
pip install flask
```

Alusta tietokanta `init-db` komennolla.
Tämä komento poistaa kaikki tiedot jos
tietokanta on jo olemassa.

```
flask --app ruokareseptit init-db
```

Käynnistä sovellus `flask run` komennolla. Sovelluksen
testaamista varten kts. lisäohjeet alla kohdassa
"Testaaminen".

```
flask --app ruokareseptit run
```

Sovellus on tämän jälkeen käytettävissä osoitteessa `http://localhost:5000/`

## Testaaminen

Sovellukseen voi syöttää suuren määärän satunnaisia käyttäjiä, reseptejä
ja arvosteluita projektin juuressa olevalla `seed.py` apuohjelmalla.
Tietokannan skeeman tulee olla alustettuna ennen tätä `init-db` komennolla.
Testidatalla tietokannan tiedostokoko kasvaa ~700 MiB kokoluokkaan.

```
flask --app ruokareseptit init-db
python3 seed.py
```

Käynnistä sovellus debug tilaan, jolloin sisäänkirjautuminen
ei tarkista salasanaa. Tämä mahdollistaa kirjautumisen testikäyttäjillä,
joilla ei ole mitään toimivaa salasanaa. Debug tilassa flask ohjelman
tulosteessa (konsolissa) näkyy myös tehdyt SQL-kyselyt.

```
flask --app ruokareseptit --debug run
```

Testikäyttäjien nimet on `test_N`, missä N on 1 ja 10000 väliltä. Jokainen
testikäyttäjä tekee useamman reseptin satunnaisella sisällöllä, sekä antaa
arvosteluita toisista resepteistä. `seed.py` luo lisäksi miljoona
`nobody_N` käyttäjää, joilla ei ole omia reseptejä mutta ovat antaneet
arvosteluita.

## Asetukset ja tuotantoon vieminen

Sovelluksen oletusasetukset on määritelty tiedostossa
`ruokareseptit/default_settings.py`. Tämä on osa
versionhallintaa, joten sinne ei tule määritellä mitään
asennuskohtaisia tai salassa pidettäviä asetuksia.

Asennuskohtaiset asetukset luetaan tiedostosta 
`instance/config.py`. Näillä voidaan yliajaa sovelluksen
oletusasetuksia.

Esimerkiksi `SECRET_KEY` asetuksen arvoa käytetään sessioevästeiden
allekirjoittamisessa. Tuotantokäytössä tälle tulee asettaa
satunnainen arvo, joka kuitenkin säilyy sovelluksen käynnistyskerrasta
toiseen, jotta käyttäjien sessiot eivät katkea.

Tämä tehdään lisäämällä `instance/config.py` tiedostoon esimerkiksi
alla näkyvän komennon tuloste. 

```
python -c 'import secrets; print("SECRET_KEY =",secrets.token_hex())'
```

## Hakemistorakenne

Sovellus on toteutettu Python pakettina, joka löytyy
sovelluksen juuresta `ruokareseptit` hakemistosta.

```
/polku/sovelluksen/juureen/
├── ruokareseptit/              # sovelluksen paketti
│   ├── __init__.py             # flask app sovellustehdas
│   ├── db.py                   # tietokannan käsittely
│   ├── default_settings.py     # sovelluksen asetukset
│   ├── schema.sql              # tietokannan skeema
│   ├── auth.py                 # pääsyoikeuksien käsittely
│   ├── xxx.py                  # jne. muut toiminnot
│   ...
│   ├── templates/
│   │   ├── base.html           # yhteinen sivupohja
│   │   ├── auth/
│   │   │   ├── login.html      # auth.py vastaavat näkymät
│   │   │   └── register.html   # esim.
│   │   ├── xxx/
│   │   │   ├── toiminto.html   # jne. muiden toimintojen näkymät
│   │   │   └── index.html      # ryhmiteltyinä omiin polkuihin
│   │   ...
│   │
│   └── static/
│       └── style.css           # sovelluksen CSS tyylit
├── instance/
│   ├── ruokareseptit.sqlite    # SQLite tietokanta
│   └── config.py               # asennuskohtaiset asetukset
├── venv/                       # käyttäjän asentama venv ympäristö
└── README.md                   # projektin kuvaus ja asennusohjeet
```

Hakemistot `instance` ja `venv` eivät ole osa versionhallintaa. Ne
syntyvät automaattisesti sovelluksen alustuksen yhteydessä. 
Kts. asennusohjeet edellä.

## Vaatimusmäärittely

### Tekniset perusvaatimukset

* Sovellus on toteutettu Python-kielellä ja Flask-kirjastoa käyttäen.
* Sovellus käyttää SQLite-tietokantaa.
* Sovelluksen käyttöliittymä muodostuu HTML-sivuista.
* Sovelluksessa ei ole käytetty JavaScript-koodia.
* Tietokantaa käytetään suoraan SQL-komennoilla (ei ORMin kautta).
* Sovellus ei käytä kirjaston flask lisäksi muita erikseen asennettavia kirjastoja.

### Sovelluksen turvallisuus

* Salasanat tallennetaan tietokantaan asianmukaisesti
* Käyttäjän oikeus nähdä sivun sisältö tarkastetaan
* Käyttäjän oikeus lähettää lomake tarkastetaan
* Käyttäjän syötteet tarkastetaan ennen tietokantaan lisäämistä
* SQL-komennoissa käytetty parametreja
* Sivut muodostetaan sivupohjien kautta
* Lomakkeissa on estetty CSRF-aukko
