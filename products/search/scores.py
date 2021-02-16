# a location match is the most important
exact_location_score = 100
inclusive_location_score = exact_location_score // 2

primary_similarweb_location = inclusive_location_score // 2
secondary_similarweb_location = primary_similarweb_location // 4

# a job function match is more important than both generic and international products
job_function_score = inclusive_location_score // 2
descendant_job_functions_score = job_function_score // 2

# generic boards that match location are next in line
is_generic_score = job_function_score // 3

# international boards last, with then without job function
is_international_score = inclusive_location_score // 6

# industry match is least important
industry_score = is_international_score // 2
