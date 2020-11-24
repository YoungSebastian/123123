import logging
import dateparser
import requests as req

from time import sleep
from datetime import date
from bs4 import BeautifulSoup
from requests_html import HTMLSession 
from psycopg2.extras import Json
from psycopg2.errors import UniqueViolation

from base import Base

logging.basicConfig(filename='../logs/'+date.today().strftime('%d-%m-%Y')+'_pracujpl',
            format='%(asctime)s %(message)s', 
            datefmt='%H:%M:%S',
            level=logging.DEBUG)

class PracujPl(Base):

    BASE_URL = 'https://www.pracuj.pl/'
    START_URL = 'https://www.pracuj.pl/praca/it%20-%20rozw%c3%b3j%20oprogramowania;cc,5016/programowanie;cc,5016003/ostatnich%2024h;p,1?rd=30'
    
    CATEGORIES = [i.replace('\n','') for i in open('./categories.txt','r').readlines()]
    TECHNOLOGIES = [i.replace('\n','') for i in open('./technologies.txt','r').readlines()]

    requests = HTMLSession()

    def scrapp_jobs_from_page(self): 
        r = self.requests.get(self.START_URL)
        r.html.render()
        logging.info('INIT '+self.START_URL)

        while True:
            job_offers = r.html.find('#results ul .results__list-container-item .offer')
            for offer in job_offers:
                offer_soup = BeautifulSoup(offer.html, 'html.parser')
                self.parse_and_insert_data(offer_soup)
                self.conn.commit()
                sleep(6)
                
            next_page = r.html.find('.pagination_element--next .pagination_trigger', first=True)
            if next_page is not None:
                next_page = next_page.absolute_links.pop()
            else:
                break

            sleep(30)
            r = self.requests.get(next_page)
            r.html.render()
            logging.info('NEXT PAGE '+next_page)
        
        logging.warning('FINITO!!!')
        self.conn.close()
    
    def parse_and_insert_data(self, soup):
        title = soup.select_one('.offer-details__title-link')

        company_name = soup.select_one('.offer-company__name')
        if company_name is not None:
            company_name = company_name.get_text().strip()
        company_city = soup.select_one('.offer-labels__item--location')
        if company_city is not None:
            company_city = company_city.get_text().replace('\n','').strip()
        
        if soup.select_one('.offer-labels__item--remote-work'):
            working_places = ['Remote']
        else:
            working_places = []
        if company_city:
            working_places.append(company_city)

        if title is not None:
            title_lower = title.get_text().lower()
        else:
            title_lower = ''

        for elem in self.CATEGORIES:
            if elem in title_lower:
                category = elem
            else:
                category = None
        
        if 'junior' in title_lower: 
            seniority = Json('junior')
        elif 'mid' or 'regular' in title_lower: 
            seniority = Json('mid')
        elif 'senior' in title_lower: 
            seniority = Json('senior')
        else: 
            seniority = None

        if soup.select_one('.offer-details__badge-name--remoterecruitment') is not None:
            online_interview = True
        else:
            online_interview = False

        article_added = soup.select_one('.offer-actions__date')
        if article_added is not None:
            article_added = article_added.get_text().replace('opublikowana: ','').replace('\n','')
            article_added = dateparser.parse(article_added)

        url = title.get('href')
        if url is None:
            job_offers_ = soup.select('.offer-regions__label')
            if job_offers_ is not None:
                url = job_offers_[0].get('href')
            for offer_ in job_offers_:
                working_places.append(offer_.get_text().strip())

        r = req.get(url)
        soup = BeautifulSoup(r.content,'html.parser')
        logging.info('OFFER: '+url)

        salary_type = None
        company_street = None
        features = soup.select('li[data-test="sections-benefit-list-item"]')
        for i in features:
            i_lower = str(i).lower()
            if 'sections-benefit-remote' in i_lower and not 'Remote' in working_places:
                working_places.append('Remote')
            elif 'sections-benefit-contracts' in i_lower:
                if 'b2b' in i_lower:
                    salary_type = 'b2b'
                elif 'pracę' in i_lower:
                    salary_type = 'pernament'
                elif 'dzieło' in i_lower:
                    salary_type = 'contact'
                else:
                    salary_type = None
            elif 'sections-benefit-workplaces' in i_lower:
                s = BeautifulSoup(i_lower, features="html.parser")
                company_street = s.find('a')
                if company_street is not None:
                    company_street = company_street.get_text()

        
        title = title.get_text()
        salary_currency = None
        salary_from = soup.select_one('.OfferView37GVCA')
        if salary_from is not None:
            salary_from = int(''.join([i for i in salary_from.get_text() if i.isdigit()]))
        salary_to = soup.select_one('span[data-test="text-earningAmountValueTo"]')
        if salary_to is not None and len(salary_to) >= 0:
            salary_to = salary_to.get_text().split()
            salary_to = int(''.join([i for i in salary_to[0] if i.isdigit()]))

        description = soup.select_one('div[data-test="section-mobileOfferContent"]')
        if description is not None:
            description = description.get_text().replace('\n',' ').lower()
            splited_description = description.split()
        else:
            splited_description = ['other']
        
        skills = []
        for tech in self.TECHNOLOGIES:
            if tech in splited_description:
                skills.append(tech)
        skills = Json(skills)

        salary_currency = 'PLN'

        if working_places:
            working_places = Json(working_places)
        try:
            self.c.execute("""INSERT INTO work (title, skills, seniority, url, 
                working_places, salary_from, salary_to, salary_type, salary_currency,
                online_interview, company_name, company_city, company_street, 
                article_added, regions, description) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
                (title, skills, seniority, url, working_places, salary_from, salary_to, salary_type, salary_currency, 
                online_interview, company_name, company_city,company_street, article_added,Json('pl'), description))
        except UniqueViolation:
            logging.warning('UNIQUE OFFER TRIED TO INSERT: '+url)

PracujPl().scrapp_jobs_from_page()