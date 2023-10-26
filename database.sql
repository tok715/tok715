create table if not exists message
(
    id         bigint auto_increment
        primary key,
    user_id    varchar(128) not null,
    user_group varchar(128) not null,
    user_name  varchar(128) not null,
    content    text         null,
    ts         bigint       not null
);

create index idx_message_user_group
    on message (user_group);

create index idx_message_user_id
    on message (user_id);

