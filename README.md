# Ruokareseptit

## Sovelluksen toiminnot

* Sovelluksessa käyttäjät pystyvät jakamaan ruokareseptejään. Reseptissä lukee tarvittavat ainekset ja valmistusohje.
* Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
* Käyttäjä pystyy lisäämään reseptejä ja muokkaamaan ja poistamaan niitä.
* Käyttäjä näkee sovellukseen lisätyt reseptit.
* Käyttäjä pystyy etsimään reseptejä hakusanalla.
* Käyttäjäsivu näyttää, montako reseptiä käyttäjä on lisännyt ja listan käyttäjän lisäämistä resepteistä.
* Käyttäjä pystyy valitsemaan reseptille yhden tai useamman luokittelun (esim. alkuruoka, intialainen, vegaaninen).
* Käyttäjä pystyy antamaan reseptille kommentin ja arvosanan. Reseptistä näytetään kommentit ja keskimääräinen arvosana.

## Sovelluksen asennus

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

Käynnistä sovellus `flask run` komennolla.

```
flask --app ruokareseptit --debug run
```

Sovellus on tämän jälkeen käytettävissä osoitteessa `http://localhost:5000/`

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

## Sovelluksen hakemistorakenne

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
