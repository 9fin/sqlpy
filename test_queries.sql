-- name: test_select
-- testing the sqlpi module pls work
-- second line comment
select *
-- comment in middle
from public.actor
limit 1;






-- name: test_select2
-- testing multiple spaces between query defs
select * from public.actor limit 1;

-- name: get_actors_by_first_name
select * 
from public.actor 
where first_name = %s
order by actor_id;

-- name: insert_actor<!>
delete from public.actor where first_name = %s and last_name = %s;
insert into public.actor (first_name, last_name)
values (%s, %s)
RETURNING first_name, last_name;

-- name: delete_actors!
delete from public.actor where first_name = %s and last_name = %s;

-- name: insert_actors<!>
insert into public.actor (first_name, last_name) values %s RETURNING first_name, last_name;

-- name: insert_country!
insert into public.country (country) values (%(country)s);

-- name: delete_country!
delete from public.country where country = %(country)s;

-- name: customers_or_staff_in_country$
select first_name, last_name, country
from public.customer c, public.address a, public.city ci, public.country co
where c.address_id = a.address_id
and a.city_id = ci.city_id
and ci.country_id = co.country_id
and (co.country = ANY(%(countires)s) or first_name = %(extra_name)s)
and ((FALSE or co.country = %(unmatched_arg)s) or (FALSE or %(unmatched_arg_trigger)s))

-- name: customers_or_staff_in_country_sort
select first_name, last_name, country
from public.customer c, public.address a, public.city ci, public.country co
where c.address_id = a.address_id
and a.city_id = ci.city_id
and ci.country_id = co.country_id
and (co.country = ANY(%(countires)s) or first_name = %(extra_name)s)
order by {} asc;



-- name: get_actors_by_first_name_exp
select * 
from public.actor 
where first_name = %s
order by actor_id "EXCEPTION";

-- name: insert_actor_exp<!>
delete from public.actor where first_name = %s and last_name = %s;
insert into public.actor (first_name, last_name)
values (%s, %s)
RETURNING first_name, last_name "EXCEPTION";

-- name: insert_country_exp!
insert into public.country (country) values (%(country)s) "EXCEPTION";

-- name: delete_country_exp!
delete from public.country where country = %(country)s "EXCEPTION";

-- name: customers_or_staff_in_country_exp$
select first_name, last_name, country
from public.customer c, public.address a, public.city ci, public.country co
where c.address_id = a.address_id
and a.city_id = ci.city_id
and ci.country_id = co.country_id
and (co.country = ANY(%(countires)s) or first_name = %(extra_name)s) "EXCEPTION"

-- name: customers_or_staff_in_country_sort_exp
select first_name, last_name, country
from public.customer c, public.address a, public.city ci, public.country co
where c.address_id = a.address_id
and a.city_id = ci.city_id
and ci.country_id = co.country_id
and (co.country = ANY(%(countires)s) or first_name = %(extra_name)s)
order by {} asc "EXCEPTION";


-- name: inventory_check@
film_in_stock

-- name: inventory_check_exp@
film_in_stock "EXCEPTION"
