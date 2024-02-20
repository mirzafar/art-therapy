create table categories
(
    id       serial
        primary key,
    title    text,
    attempt  smallint,
    position smallint,
    type     varchar(10)
);

create table questions
(
    id          serial
        primary key,
    text        text,
    category_id integer  not null
        constraint questions_categories_id_fk
            references categories,
    buttons     jsonb[],
    position    smallint not null
        unique,
    media       jsonb,
    details     jsonb
);


create table tunes
(
    id     serial
        primary key,
    title  text,
    path   text,
    status smallint default 1 not null,
    genre  varchar(50),
    words  text[]   default '{}'::text[]
);

create table customers
(
    id       serial
        primary key,
    name     text,
    username text,
    uid      text,
    status   smallint default 1
);

create table kbase
(
    id       serial
        primary key,
    response text,
    type     varchar(100),
    title    text
);

create table playlist
(
    id          serial
        primary key,
    turn_id     integer,
    type        varchar(150),
    customer_id integer,
    title       text,
    url         text,
    status      smallint default 0,
    words       text[]
);

create table orders
(
    id      serial
        primary key,
    path    text,
    chat_id text,
    status  smallint default 0,
    words   text[],
    url     text
);

