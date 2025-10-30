Logo
Ask or search…
⌘
k
Contact us
More
Documentation
Self-service
Release notes


Copy

Employee API
Multi-source Employee API
Data Dictionary: Multi-source Employee API
On this page, you'll find detailed information about Coresignal's Multi-source Employee data.
Each category includes a table listing the available data points, their explanations, data types, and sample code snippets.

All personal/company information mentioned within this context is entirely fictional and is solely intended for illustrative purposes.

Data points in the example snippets are rearranged for better grouping.

Data points per category
Metadata

Identifiers and URLs

Employee information

Professional contact information

Locations

Experience and workplace

Full experience information

Workplace details

Education

Salary

Profile field changes

Recent experience changes

Recommendations

Activity

Awards

Courses

Certifications

Languages

Patents

Publications

Projects

Organizations

Metadata
Data point
Description
Data type
created_at

The date and time when the employee record was created

String (date)

updated_at

The date and time when the employee record was last fully updated

String (date)

checked_at

The date and time when the employee record was last checked partially

String (date)

changed_at

The date and time when the employee record was last changed

String (date)

experience_change_last_identified_at

The date and time when the employee record change was last identified

String (date)

is_deleted

Marks if the employee record is deleted or private
1 – the record is deleted
0 – the record is not deleted

Number (integer)

is_parent

Notes if the employee record is the main employee profile:
1 – the record is parent (main)
0 – the record is not parent

Number (integer)

See a snippet of the dataset for reference:

Metadata

Copy
    "created_at": "2024-07-27T01:56:27.000",
    "updated_at": "2024-10-23T05:50:09.000",
    "checked_at": "2025-09-23T05:50:09.000",
    "changed_at": "2025-10-01T06:30:1.000",
    "experience_change_last_identified_at": "2024-10-25T06:30:10.000",
    "is_deleted": 0,
    "is_parent": 1
Identifiers and URLs
Data point
Description
Data type
id

Coresignal's identification key for an employee profile record.
Taken from the professional network dataset.

Number (integer)

parent_id

Parent category identification key

Number (integer)

historical_ids

Historical identification keys that are related to the same profile after URL change

Array of strings

professional_network_url

Most recent profile URL on professional network

String

professional_network_shorthand_names

Historical variations of shorthand names for the employee

Array of strings

public_profile_id

Public profile ID

Number (long)

See a snippet of the dataset for reference:

Identifiers & URLs

Copy
"id": 12389891,
"parent_id": 12389891,
"public_profile_id": 123456789, 
"historical_ids": [
  12389891,
  11589843
],
"professional_network_url": "https://www.professional_network.com/in/john-doe-18729383",
"professional_network_shorthand_names": [
  "real-john-doe"    
  "john-doe-1992"  
],
Employee information
Data point
Description
Data type
full_name

Employee's full name

String

first_name

Employee's first name
Parsed from the full_name

String

first_name_initial

First name initial
Parsed from first_name

String

middle_name

Employee's middle name
Parsed from the full_name

String

middle_name_initial

Middle name initial
Parsed from middle_name

String

last_name

Employee's last name
Parsed from the full_name

String

last_name_initial

Last name initial
Parsed from last_name

String

picture_url

Picture URL

String

connections_count

Count of profile connections

Number (integer)

followers_count

Count of profile followers

Number (integer)

interests

Employee's interests

Array of strings

See a snippet of the dataset for reference:

Employee information

Copy
"full_name": "John Doe",
"first_name": "John",
"first_name_initial": "J",
"middle_name": "Michael",
"middle_name_initial": "M",
"last_name": "Doe",
"last_name_initial": "D",
"picture_url": "https://static.lnk.com/aero-v1/sc/h/9c8pery4andzj6ohjkjp54ma2" 
"connections_count": 472,
"followers_count": 3190,
"interests": 
[
    "hiking",
    "snowboarding",
    "cycling",
]
Professional contact information
Coresignal collects only publicly available, strictly business-related data published or released by companies or individuals at their discretion online. The contact information includes only professional emails.
No sensitive or private/ located within the login secured areas information is collected or transmitted.

Data point
Description
Data type
primary_professional_email

Employee's business email address tied to their workplace

String

primary_professional_email_status

The confidence level in the accuracy of the employee's business email address. The field will return four options: verified, matched_email, ``matched_pattern, orguessed_common_pattern.

String

professional_emails_collection

Collection of employee's business email addresses

Array of structs

professional_email

Employee's business email address

String

professional_email_status

The confidence level in the accuracy of the employee's professional email address. The field will return four options:

 verified – the email was matched and verified

matched_email – the email was matched but could not retrieve "verified" status

matched_pattern – the exact email was not matched, but it was guessed based on the matched email pattern for the company

guessed_common_pattern – neither the exact email nor the email pattern for that company was matched, but the most common global pattern was guessed

String

order_of_priority

Order of priority based on confidence in email validity

Number (integer)

See a snippet of the dataset for reference:

Professional contact information

Copy
"primary_professional_email": "johndoe@company1.com", 
"primary_professional_email_status": "matched_pattern",
"professional_emails_collection": [
    {
        "professional_email": "johndoe@company1.com",
        "professional_email_status": "matched_pattern",
        "order_of_priority": 1
    },
    {
        "professional_email": "john.doe1@company1.com",
        "professional_email_status": "matched_pattern",
        "order_of_priority": 2
    },
    {
        "professional_email": "johndoe123@company1.com",
        "professional_email_status": "matched_pattern",
        "order_of_priority": 3
    }
]
Location
Data point
Description
Data type
location_country

Associated country

String

location_city

Employee location city

String

location_state

Employee location state

String

location_country_iso2

ISO 2-letter code of the location country, based on their location_country value.

String

location_country_iso3

ISO 3-letter code of the location country, based on their location_countryvalue.

String

location_full

Full location

String

location_regions

Associated geographical regions based on their location_country value

Array of strings

See a snippet of the dataset for reference:

Location

Copy
"location_country": "United States",
"location_city": "San Diego",
"location_state": "California",
"location_country_iso2": "US",
"location_country_iso3": "USA",
"location_full": "San Diego, California, United States",
"location_regions": [
    {
        "region": "Americas"
    },
    {
        "region": "Northern America"
    },
    {
        "region": "AMER"
    }
]
Experience and workplace
Active experience overview
Data point
Description
Data type
headline

Profile headline

String

summary

Main description (employee summary)

String

services

Offered services

String

is_working

Marks if the employee is currently employed
1 – the employee is currently working
0 – the employee is currently not working

Number (integer)

active_experience_company_id

Coresignal's identification key for a company to identify where the employee is currently working

Number (integer)

active_experience_title

Title of employee's current position

String

active_experience_description

Description of the current position

String

active_experience_department

A list of employee's departments, based on actve_position_title

String

active_experience_management_level

A list of employee's management levels, based on active_experience_title

String

is_decision_maker

Marks if the employee is a decision maker, based on active_experience_title
1 – the employee is a decision maker
0 – the employee is not a decision maker

Number (integer)

See a snippet of the dataset for reference:

Active experience overview

Copy
"headline": "Data Analyst | Machine Learning Enthusiast",
"generated_headline": "Data Specialist – Predictive Analytics",
"summary": "<p>Passionate about uncovering insights from data and applying machine learning techniques to solve global problems.</p>",
"services": "Data Analysis, Machine Learning Consulting, Business Intelligence",
"is_working": 1,
"active_experience_company_id": 4127532,
"active_experience_title": "Senior Data Analyst",
"active_experience_description": "Leading data-driven projects, building predictive models, and optimizing business intelligence strategies.",
"active_experience_department": "Engineering and Technical",
"active_experience_management_level": "Senior",
"is_decision_maker": 1
Skills
Data point
Description
Data type
inferred_skills

Lists employees' skills based on the descriptions from the profile

Array of strings

historical_skills

Historical skills

Array of strings

See a snippet of the dataset for reference:

Skills

Copy
"inferred_skills": [
    "cloud computing",
    "data analysis",
    "deep learning",
    "software development",
    "system architecture",
    "troubleshooting",
    "web development"
]
Experience duration
Data point
Description
Data type
total_experience_duration_months

Total normalized experience duration of all Employee's experiences

Number (integer)

total_experience_duration_months_breakdown_department

Total normalized experience duration by employee's department

Array of structs

department

Department

String

total_experience_duration_months

Experience duration in months

String

total_experience_duration_months_breakdown_management_level

Total normalized experience duration by Employee's management level

Array of structs

management_level

Employee's management level

String

total_experience_duration_months

Experience duration in months

String

See a snippet of the dataset for reference:

Experience duration

Copy
"total_experience_duration_months": 85,
"total_experience_duration_months_breakdown_department": [
    {
        "department": "C-Suite",
        "total_experience_duration_months": 13
    },
    {
        "department": "Marketing",
        "total_experience_duration_months": 30
    },
    {
        "department": "Finance & Accounting",
        "total_experience_duration_months": 14
    },
    {
        "department": "Engineering and Technical",
        "total_experience_duration_months": 28
    }
],
"total_experience_duration_months_breakdown_management_level": [
    {
        "management_level": "C-Level",
        "total_experience_duration_months": 10
    },
    {
        "management_level": "Intern",
        "total_experience_duration_months": 3
    },
    {
        "management_level": "Senior",
        "total_experience_duration_months": 4
    },
    {
        "management_level": "Specialist",
        "total_experience_duration_months": 40
    },
    {
        "management_level": "Manager",
        "total_experience_duration_months": 18
    }
]
Full experience information
Data point
Description
Data type
experience

Work experience the Employee has

Array of structs

active_experience

Identifies if this is a current (active) position

String

position_title

Employee's position title

String

department

Employees department

String

management_level

Employee's management level

String

location

Job/workplace location

String

date_from

Employment start date

String (date)

date_from_year

Employment start year

Integer

date_from_month

Employment start month

Integer

date_to

Employment end date

String (date)

date_to_year

Employment end year

Integer

date_to_month

Employment end month

Integer

duration_months

Employment duration in months

Integer

description

Employment description

String

See a snippet of the dataset for reference:

Full experience information

Copy
"experience": [
    {
        "active_experience": 0,
        "position_title": "Senior Data Analyst",
        "department": "Data Science",
        "management_level": "Mid-Level",
        "location": "San Francisco, California, United States",
        "date_from": "March 2020",
        "date_from_year": 2020,
        "date_from_month": 3,
        "date_to": "July 2022",
        "date_to_year": 2022,
        "date_to_month": 7,
        "duration_months": 126
    }
]
Workplace details
Metadata and firmographics
Data point
Description
Data type
company_id

Company record identification key in Coresignal's database

Integer

company_name

Company name

String

company_type

Company type

String

company_founded_year

Founding year

String (date)

company_size_range

Company size based on employee count range (as selected by the company profile administrator)

String

company_employees_count

Number of employees that associated their experience with the company

Integer

company_categories_and_keywords

Categories and keywords are assigned to the company profile and products across various platforms

Array of strings

company_employees_count_change_yearly_percentage

Company employee count change (percentage)

Number (double)

company_industry

Company's industry

String

company_last_updated_at

The last update date of the record in the YYYY-MM-DD format

String (date)

company_is_b2b

Indicates if the company operates in a business-to-business model:
1 – b2b company
0 – b2c company

Integer

order_in_profile

The order number of the workplace in the profile

Integer

See a snippet of the dataset for reference:

Metadata & firmographics

Copy
"company_id": 87272276,
"company_name": "Company123, LLC",
"company_type": "Privately Held",
"company_founded_year": "2023",
"company_size_range": "51-200 employees",
"company_employees_count": 157,
"company_categories_and_keywords": [
                "Data Analysis",
                "AI",
                "Management",
                "Consulting",
],
"company_employees_count_change_yearly_percentage": 17.43222222222222
"company_industry": "Manufacturing",
"company_last_updated_at": "2025-02-03", 
"company_is_b2b": 1,
"order_in_profile": 1
Social media
Data point
Description
Data type
company_followers_count

Company's profile follower count on professional network

Integer

company_website

Company's website

String

company_facebook_url

Company's Facebook URL

Array of strings

company_twitter_url

Company's X (Twitter) URL

Array of strings

company_linkedin_url

Company's LinkedIn URL

String

See a snippet of the dataset for reference:

Social media

Copy
"company_followers_count": 527712,
"company_website": "https://www.company1.com",
"company_facebook_url": [
    "https://www.facebook.com/company1global",
    "https://www.facebook.com/company1"
],
"company_twitter_url": [
    "https://www.x.com/company1"
],
"company_linkedin_url": "https://www.linkedin.com/company/company1"
Financials
Data point
Description
Data type
company_annual_revenue_source_1
company_annual_revenue_source_5

Company's revenue from a specific source

Array of objects

company_annual_revenue_currency_source_1

company_annual_revenue_currency_source_5

Revenue currency

String

company_last_funding_round_date

Date when the last funding round was announced in YYYY-MM-DD format

String (date)

company_last_funding_round_amount_raised

Amount raised in the last funding round

Integer (long)

company_stock_ticker

Company's stock ticker information

Array of objects

exchange

Stock exchange

String

ticker

Stock ticker

String

See a snippet of the dataset for reference:

Financials

Copy
"annual_revenue_source_5": 32590000,
"annual_revenue_currency_source_5": "$",
"annual_revenue_source_1": 878728373,
"annual_revenue_currency_source_1": "$",

"company_last_funding_round_date": "2014-03-25",
"company_last_funding_round_amount_raised": 200 000,

"stock_ticker": [
    {
      "exchange": "NASDAQ", 
      "ticker": "AAPL" 
    }
  ]
Workplace locations
Data point
Description
Data type
company_hq_full_address

Full address of the company's headquarters

String

company_hq_country

The country where the company's headquarters is located

String

company_hq_regions

Detailed region where the company's headquarters is located

Array of strings

company_hq_country_iso2

ISO 2-letter code of the headquarters country

String

company_hq_country_iso3

ISO 3-letter code of the headquarters country

String

company_hq_city

Headquarters city

String

company_hq_state

Headquarters state

String

company_hq_street

Headquarters street address

String

company_hq_zipcode

Headquarters zip code

String

See a snippet of the dataset for reference:

Locations

Copy
"company_hq_full_address": "123 Data Drive, Analytics City, CA 94016, USA",
"company_hq_country": "United States",
"company_hq_regions": [
                "Americas",
                "Northern America",
                "AMER"],
"company_hq_country_iso2": "US",
"company_hq_country_iso3": "USA",
"company_hq_city": "Analytics City",
"company_hq_state": "California",
"company_hq_street": "123 Data Drive",
"company_hq_zipcode": "94016",
Education
Data point
Description
Data type
last_graduation_date

Last graduation date

String (date)

education_degrees

List of education degrees held by the person

Array of strings

education

Employee's education

Array of objects

degree

Degree name

String

description

Degree description

String

institution_url

Institution's profile URL

String

institution_name

Institution's name

String

institution_full_address

Institution's full address

String

institution_country_iso2

ISO 2-letter code of the institution's country

String

institution_country_iso3

ISO 3-letter code of the institution's country

String

institution_regions

Institution's region

Array of strings

institution_city

Institution's city

String

institution_state

Institution's state

String

institution_street

Institution's street

String

institution_zipcode

Institution's zip code

String

date_from_year

Enrollment date

Number (integer)

date_to_year

Graduation date

String (date)

activities_and_societies

Activities and societies that are connected with the employee

String

order_in_profile

Order in profile

Number (integer)

See a snippet of the dataset for reference:

Education

Copy
"last_graduation_date": 2022,
  "education_degrees": [
    "Bachelor of Science, Computer Science Engineering, 9.12 (Rank: 4/80)",
    "Senior Secondary, Mathematics, 93%",
    "Higher Secondary, Science, 96%"
  ],
  "education": [
    {
      "degree": "Bachelor of Science, Computer Science Engineering, 9.12 (Rank: 4/80)",
      "description": "Focused on core sciences with a strong foundation in Physics and Chemistry.",
      "institution_url": "https://www.topuniversity.edu",
      "institution_name": "Top University",
      "institution_full_address": "Top University, 123 Main St, Cityville, State 12345, USA",
      "institution_country_iso2": "US",
      "institution_country_iso3": "USA",
      "institution_regions": [
        "North America",
        "East Coast"
      ],
      "institution_city": "Cityville",
      "institution_state": "State",
      "institution_street": "123 Main St",
      "institution_zipcode": "12345",
      "date_from_year": 2014,
      "date_to_year": 2016,
      "activities_and_societies": "Science Fair, Debate Team",
      "order_in_profile": 1
    },
    ]
Salary
Projected base salary
Data point
Description
Data type
projected_base_salary_p25

Minimum projected base salary for the current position (25th percentile)

Number (double)

projected_base_salary_median

Median projected base salary for the current position

Number (double)

projected_base_salary_p75

Maximum projected base salary for the current position (75th percentile)

Number (double)

projected_base_salary_period

Data collection period

String

projected_base_salary_currency

Salary currency

String

projected_base_salary_updated_at

Data last update date

String (date)

See a snippet of the dataset for reference:

Projected base salary

Copy
"projected_base_salary_p25": 105432.56,
"projected_base_salary_median": 120785.90,
"projected_base_salary_p75": 145430.78,
"projected_base_salary_period": "ANNUAL",
"projected_base_salary_currency": "USD",
"projected_base_salary_updated_at": "2025-02-03"
Projected additional salary
Data point
Description
Data type
projected_additional_salary

Projected additional salary

Array of structs

projected_additional_salary_type

Projected additional salary type for the current position

String

projected_additional_salary_p25

Minimum projected additional salary for the current position (25th percentile)

Number (double)

projected_additional_salary_median

Median projected additional salary for the current position

Number (double)

projected_additional_salary_p75

Maximum projected additional salary for the current position (75th percentile)

Number (double)

projected_additional_salary_period

Data collection period

String

projected_additional_salary_currency

Salary currency

String

projected_additional_salary_updated_at

Data last update date

String (date)

See a snippet of the dataset for reference:

Projected additional salary

Copy
"projected_additional_salary": [
    {
        "projected_additional_salary_type": "Cash Bonus",
        "projected_additional_salary_p25": 7654.21,
        "projected_additional_salary_median": 10234.56,
        "projected_additional_salary_p75": 14123.78
    },
    {
        "projected_additional_salary_type": "Stock Bonus",
        "projected_additional_salary_p25": 8892.10,
        "projected_additional_salary_median": 11754.93,
        "projected_additional_salary_p75": 16123.12
    }
]
"projected_additional_salary_period": "ANNUAL",
"projected_additional_salary_currency": "USD",
"projected_additional_salary_updated_at": "2024-12-06"
Projected total salary
Data point
Description
Data type
projected_total_salary_p25

Minimum projected total salary value for the current position (25th percentile)

Number (double)

projected_total_salary_median

Median projected total salary value for the current position

Number (double)

projected_total_salary_p75

Maximum projected total salary value for the current position (75th percentile)

Number (double)

projected_total_salary_period

Data collection period

String

projected_total_salary_currency

Salary currency

String

projected_total_salary_updated_at

Data last update date

String (date)

See a snippet of the dataset for reference:

Projected total salary

Copy
"projected_total_salary_p25": 142763.21,
"projected_total_salary_median": 153290.88,
"projected_total_salary_p75": 165432.19,
"projected_total_salary_period": "ANNUAL",
"projected_total_salary_currency": "USD",
"projected_total_salary_updated_at": "2025-02-12",
Profile field changes
Data point
Description
Data type
profile_root_field_changes_summary

Summary of the field-level changes

Array of structs

field_name

Name of the data field

String

change_type

Type of the data field change

String

last_changed_at

Date of the last data field change

String (date)

profile_collection_field_changes_summary

Summary of changes in profile collection fields

Array of structs

field_name

Name of the collection data field

String

last_changed_at

Data of the last collection data field change

String

See a snippet of the dataset for reference:

Profile field changes

Copy
"profile_root_field_changes_summary": [
    {
        "field_name": "followers_count",
        "change_type": "updated",
        "last_changed_at": "2023-07-18T09:22:45.567"
    },
    {
        "field_name": "summary",
        "change_type": "updated",
        "last_changed_at": "2025-02-18T09:22:45.567"
    }
],
"profile_collection_field_changes_summary": [
    {
        "field_name": "experience",
        "last_changed_at": "2024-01-05T17:48:12.892"
    },
    {
        "field_name": "activity",
        "last_changed_at": "2025-02-05T17:48:12.892"
    }
]
Recent experience changes
Data point
Description
Data type
experience_recently_started

Collection of identified recently started Employee experiences

Array of structs

company_id

Coresignal's identification key for a company record

String

company_name

Company name

String

company_url

Professional network URL of the company

String

company_shorthand_name

Shorthand name of the company's Professional network URL

String

date_from

Start date of the experience record

String

date_to

End date of the experience record

String

title

Position title in the company

String

identification_date

Date when experience change was identified

String

experience_recently_closed

Collection of employee experiences that ended recently

Array of structs

company_id

Coresignal's identification key for a company record

String

company_name

Company name

String

company_url

Professional network URL of the company

String

company_shorthand_name

Shorthand name of the company's Professional network URL

String

date_from

Start date of the experience record

String

date_to

End date of the experience record

String

title

Position title in the company

String

identification_date

Date when experience change was identified

String

See a snippet of the dataset for reference:

Recent experience changes

Copy
"experience_recently_started": [
    {
        "company_id": 3124502,
        "company_name": "Company1, LLC",
        "company_url": "https://www.professional_network.com/company/company1-llc",
        "company_shorthand_name": "company1-llc",
        "date_from": "Nov 2024",
        "date_to": "Dec 2024",
        "title": "Senior Software Engineer",
        "identification_date": "2024-11-19T15:34:29.412"
    },
],
"experience_recently_closed": [
    {
        "company_id": 3124504,
        "company_name": "Company3, LLC",
        "company_url": "https://www.professional_network.com/company/company3-llc",
        "company_shorthand_name": "company3-llc",
        "date_from": "Jul 2021",
        "date_to": "Oct 2024",
        "title": "Software Engineer",
        "identification_date": "2024-12-14T10:48:37.215"
    }
]
Recommendations
Data point
Description
Data type
recommendations_count

Number of recommendations from other users

Number (integer)

recommendations

List of recommendations received

Array of structs

recommendation

Recommendation text

String

referee_full_name

The full name of the person who wrote the recommendation

String

referee_url

The URL of the profile of the person who wrote the recommendation

String

order_in_profile

The exact position of the recommendation in the profile

Number (integer)

See a snippet of the dataset for reference:

Recommendations

Copy
"recommendations_count": 2,
  "recommendations": [
    {
      "recommendation": "“I had the pleasure of collaborating with John during his time at Tech Innovations, where he displayed a rare combination of creativity and technical expertise. He consistently demonstrated outstanding problem-solving skills, particularly in software engineering and AI. His attention to detail and collaborative spirit made him a valuable asset to the team. John is also a great mentor who is always ready to share his knowledge with others, making him a true team player.”",
      "referee_full_name": "Jane Doe 1",
      "referee_url": "https://www.professional_network.com/in/jane-doe-1",
      "order_in_profile": 1
    },
    {
      "recommendation": "“John’s drive and determination have impressed me from our first interaction during a project at Company1 Solutions. He has an extraordinary ability to tackle complex challenges and has a passion for both technology and team collaboration. His contributions were key to the success of several high-profile projects. He is an individual who thrives in dynamic environments and continuously seeks to innovate and improve processes.”",
      "referee_full_name": "Jane Doe 2",
      "referee_url": "https://www.professional_network.com/in/jane-doe-2",
      "order_in_profile": 2
    }
]
Activity
Data point
Description
Data type
activity

User's activity (posts)

Array of structs

activity_url

Post URL

String

title

Post title

String

action

Activity type

String

order_in_profile

The exact position of the activity in the profile

Number (integer)

See a snippet of the dataset for reference:

Activity

Copy
"activity": [
    {
      "activity_url": "https://www.professional_network.com/posts/johndoe_ai-innovations-and-the-future-of-tech-activity-1234567890123456789-XYZ",
      "title": "Excited to share my thoughts on the future of AI and its impact on industries worldwide. The advancements in machine learning are opening new doors…",
      "action": "Liked by",
      "order_in_profile": 1
    }
]
Awards
Data point
Description
Data type
awards

Awards held by the person

Array of structs

title

Award title

String

issuer

Award issuer

String

description

Award description

String

date

Award date

String

date_year

Award year

StringNumber (integer)

date_month

Award month

Number (integer)

order_in_profile

The exact position of the award in the profile

Number (integer)

See a snippet of the dataset for reference:

Awards

Copy
"awards": [
    {
        "title": "Outstanding Achievement Award",
        "issuer": "Top University",
        "description": "Recognized for exceptional contributions to student initiatives and leadership in organizing university-wide events.",
        "date": "March 15, 2024",
        "date_year": 2024,
        "date_month": 3,
        "order_in_profile": 1
    }
]
Courses
Data point
Description
Data type
courses

Courses

Array of structs

organizer

Course organizer

String

title

Course title

String

order_in_profile

The exact position of the course in the profile

Number (integer)

See a snippet of the dataset for reference:

Courses

Copy
"courses": [
    {
        "organizer": "AI Certification",
        "title": "Machine Learning Fundamentals",
        "order_in_profile": 1
    },
    {
        "organizer": "CS Academ",
        "title": "Advanced Algorithms and Data Structures",
        "order_in_profile": 2
    },
]
Certifications
Data point
Description
Data type
certifications

Certifications

Array of structs

title

Certification title

String

issuer

Certification issuer

String

issuer_url

Issuer profile URL

String

credential_id

Credential identification key

String

certificate_url

Certification URL

String

date_from

Certification issue date

String (date)

date_from_year

Issue year

Number (integer)

date_from_month

Issue month

Number (integer)

date_to

Certification expiry date

String (date)

date_to_year

Expiry year

Number (integer)

date_to_month

Expiry month

Number (integer)

order_in_profile

The exact position of the certification in the profile

Number Array

See a snippet of the dataset for reference:

Certifications

Copy
"certifications": [
    {
        "title": "Advanced Data Analysis",
        "issuer": "Certification Company 123",
        "issuer_url": "https://www.certificationcompany123.com",
        "credential_id": "EFGH98765432",
        "certificate_url": "https://www.certificationcompany123.com/certificates/f44f9027fba14efb953da9db849e5ed2",
        "date_from": "Nov 2023",
        "date_from_year": 2023,
        "date_from_month": 11,
        "date_to": "Nov 2024",
        "date_to_year": 2024,
        "date_to_month": 11,
        "order_in_profile": 1
    }
]
Languages
Data point
Description
Data type
languages

Language knowledge

Array of structs

language

Listed language

String

proficiency

Language proficiency

String

order_in_profile

The exact position of the language in the profile

Number (integer)

See a snippet of the dataset for reference:

Languages

Copy
"languages": [
    {
        "language": "English",
        "proficiency": "Full professional proficiency",
        "order_in_profile": 1
    },
    {
        "language": "Spanish",
        "proficiency": "Limited working proficiency",
        "order_in_profile": 2
    },
    {
        "language": "French",
        "proficiency": "Professional working proficiency",
        "order_in_profile": 3
    }
]
Patents
Data point
Description
Data type
patents_count

Number of authored patents

Number (integer)

patents_topics

Patent topics

Array of strings

patents

Authored patents

Array of structs

title

Patent title

String

status

Patent status

String

description

Patent description

String

patent_url

Patent URL

String

date

Patent filing date

String (date)

date_year

Filling year

Number (integer)

date_month

Filling month

Number (integer)

patent_number

Patent number

String

order_in_profile

The exact position of the patent in the profile

Number (integer)

See a snippet of the dataset for reference:

Patents count

Copy
"patents_count": 1,
"patents_topics": "Data Analysis",
"patents": [
    {
        "title": "Advanced Data Analysis Using Neural Networks",
        "status": "Granted",
        "description": "A novel approach to data analysis leveraging deep learning techniques to improve accuracy in predictive modeling and data interpretation.\\n<!---->      </p>",
        "patent_url": "https://example123.com/patent/data-analysis-neural-networks",
        "date": "September 10, 2023",
        "date_year": 2023,
        "date_month": 9,
        "patent_number": "US112233445A1",
        "order_in_profile": 1
    }
]
Publications
Data point
Description
Data type
publications_count

Count of publications authored by the employee

Number (integer)

publications_topics

Publication topics

Array of strings

publications

Authored publications

Array of structs

title

Publication title

String

description

Publication description

String

publication_url

Publication website URL

String

publisher_name

Publication publisher

Array of strings

date

Publication release date

String (date)

date_year

Release year

Number (integer)

date_month

Release month

Number (integer)

order_in_profile

The exact position of the publication in the profile

Number (integer)

See a snippet of the dataset for reference:

Publications

Copy
"publications_count": 1,
"publications_topics": [
    "Machine Learning in Healthcare Applications"
],
"publications": [
    {
        "title": "Machine Learning-Based Heart Disease Prediction",
        "description": "This research focuses on utilizing machine learning techniques to predict heart diseases by analyzing EKG signals, a part of my project from June'21 to December'21.\\n<!---->      </p>",
        "publication_url": "https://www.researchpaper123.net/publication/343632915_Machine_Learning",
        "publisher_names": [
            "John Doe",
            "Jane Doe"
        ],
        "date": "December 15, 2021",
        "date_year": 2021,
        "date_month": 12,
        "order_in_profile": 1
    }
]
Projects
Data point
Description
Data type
projects_count

Count of total projects listed in the profile

Number (integer)

projects_topics

Topics related to the projects listed in the profile

Array of strings

projects

Projects created by the profile

Array of structs

name

Project name

String

description

Project description

String

project_url

Project website URL

String

date_from

Project start date

String (date)

date_from_year

Project start year

Number (integer)

date_from_month

Project start month

Number (integer)

date_to

Project end date

String (date)

date_to_year

Project end year

Number (integer)

date_to_month

Project end month

Number (integer)

order_in_profile

The exact position of the project in the profile

Number (integer)

See a snippet of the dataset for reference:

Projects

Copy
"projects_count": 1,
"projects_topics": [
    "Predictive Analytics in Complex Systems",
    "Real-time Facial Expression Analysis for Emotional Intelligence Systems",
    "Design and Simulation of Adaptive Actuators for Smart Materials",
    "Audio Signal Separation for Enhanced Speech Recognition",
    "Non-Invasive Glucose Monitoring Using Spectroscopic Data Analysis"
],
"projects": [
    {
        "name": "Predictive Analytics for Fault Detection in Complex Mechanical Systems",
        "description": "As part of a research initiative, a predictive system was developed to identify anomalies in mechanical systems. The project utilized historical failure data and machine learning models.</p>",
        "project_url": "https://www.projecturl123.net/project/123456_Analytics",
        "date_from": "Oct 2018",
        "date_from_year": 2018,
        "date_from_month": 10,
        "date_to": "May 2019",
        "date_to_year": 2019,
        "date_to_month": 5,
        "order_in_profile": 1
    }
]
Organizations
Data point
Description
Data type
organizations

Memberships in organizations

Array of structs

organization_name

Organization title

String

position

Position in the organization

String

description

Description of the activity/experience in the organization

String

date_from

Membership start date

String (date)

date_from_year

Membership start year

Number (integer)

date_from_month

Membership start month

Number (integer)

date_to

Membership end date

String (date)

date_to_year

Membership end year

Number (integer)

date_to_month

Membership end month

Number (integer)

order_in_profile

The exact position of the organization in the profile

Number (integer)

See a snippet of the dataset for reference:

Organizations

Copy
"organizations": [
    {
        "organization_name": "Tech Club",
        "position": "Event Coordinator",
        "description": "Led and organized data-driven workshops and events, focusing on data analytics and machine learning applications in various industries.",
        "date_from": "Feb 2016",
        "date_from_year": 2016,
        "date_from_month": 2,
        "date_to": "Mar 2018",
        "date_to_year": 2018,
        "date_to_month": 2,
        "order_in_profile": 1
    }
]
Previous
Multi-source Employee API
Next
Sample: Multi-source Employee API
Last updated 14 days ago

Was this helpful?







Data Dictionary: Multi-source Employee API | Coresignal Docs