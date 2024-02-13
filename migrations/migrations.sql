create table users
(
    id          serial
        primary key,
    last_name   varchar(100) default ''::character varying,
    first_name  varchar(100) default ''::character varying,
    middle_name varchar(100) default ''::character varying,
    status      smallint     default 0,
    password    text         default ''::text not null,
    username    varchar(100)                  not null,
    photo       varchar(150) default ''::character varying,
    created_at  timestamp    default (now())::timestamp without time zone,
    birthday    date
);

create index users_password_index
    on users (password);

create index users_status_index
    on users (status);

create unique index users_username_uindex
    on users (username);

create table public.districts
(
    id     serial primary key unique not null,
    title  varchar(250),
    number smallint,
    status smallint default 0
);

create table public.regions
(
    id     serial primary key unique not null,
    title  varchar(250),
    status smallint default 0
);

alter table public.regions
    add district_id integer;

alter table public.regions
    add constraint regions_districts_id_fk
        foreign key (district_id) references public.districts;

create table public.tracks
(
    id          serial primary key unique not null,
    title       varchar(250),
    region_id   integer
        constraint table_name_regions_id_fk
            references public.regions,
    description text,
    status      smallint default 0
);




