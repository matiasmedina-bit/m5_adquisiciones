--
-- PostgreSQL database dump
--

\restrict UduJpW0zANYlRT0pE4BPr94uf8KBHuv9tvcLliIFvI7paSeNBdSUEGzZEnxOgPb

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: proveedores_proveedor; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.proveedores_proveedor VALUES (7, 'Pinturas y Revestimientos ProSur', '763456783', 'contacto@pinturas.cl', '+56 2 2345 6789', '30_DIAS', false, '2026-09-01 22:04:31.011552-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (8, 'Arriendo de Maquinaria Costa', '77456789K', 'contacto@arriendo.cl', '+56 2 2345 6789', 'CONTADO', true, '2026-09-01 22:04:31.011552-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (10, 'Seguridad y EPP Trabajo Seguro', '796789012', 'contacto@seguridad.cl', '+56 2 2345 6789', '60_DIAS', false, '2026-09-01 22:04:31.013807-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (2, 'Aceros y Fierros del Sur Ltda', '123456785', 'contacto@aceros.cl', '', '60_DIAS', false, '2026-06-05 23:31:30.061187-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (5, 'Áridos y Transportes Maipo SpA', '781234567', 'contacto@aridos.cl', '+56 2 2345 6789', '90_DIAS', true, '2026-09-01 22:04:31.010798-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (1, 'Ferretería El Constructor SpA', '111111111', 'contacto@ferreteria.cl', '', '30_DIAS', true, '2026-06-05 23:31:30.060187-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (9, 'Gasfitería y Riego Aconcagua', '785678906', 'contacto@gasfiteria.cl', '+56 2 2345 6789', '30_DIAS', true, '2026-09-01 22:04:31.013054-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (11, 'Sodimac Empresas S.A.', '96792430K', 'empresas@sodimac.cl', '+56 2 2600 1000', '30_DIAS', true, '2026-10-04 00:30:55.708538-03', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (12, 'Cementos Melón S.A.', '93248000K', 'ventas@melon.cl', '+56 2 2600 1000', '60_DIAS', true, '2026-10-04 00:30:55.709565-03', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (13, 'Ferretería Sin Correo Ltda', '771112226', '', '+56 2 2600 1000', 'CONTADO', true, '2026-10-04 00:30:55.710078-03', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (4, 'Maderas y Terciados Pucón Ltda', '778889998', 'contacto@maderas.cl', '+56 2 2345 6789', 'CONTADO', true, '2026-09-01 22:04:31.009795-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (6, 'Eléctricos Industriales Andes', '792345674', 'contacto@electricos.cl', '+56 2 2345 6789', '60_DIAS', true, '2026-09-01 22:04:31.011552-04', '', '', '', '2026-11-14 17:28:05.8704-03');
INSERT INTO public.proveedores_proveedor VALUES (3, 'Hormigones Bío-Bío S.A.', '765432103', 'contacto@hormigones.cl', '+56 2 2345 6789', '30_DIAS', true, '2026-09-01 22:04:31.006044-04', 'Concepción', 'Av. Pedro de Valdivia 1200', 'Construccion', '2026-11-14 19:07:33.252207-03');


--
-- Data for Name: proyectos_proyecto; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.proyectos_proyecto VALUES (1, 'Edificio Residencial Las Condes', 'Inmobiliaria Aurora', '2026-06-05', '2026-06-18', 'EJECUCION', 850000000, 'CC-2026-014');
INSERT INTO public.proyectos_proyecto VALUES (2, 'Centro Médico Ñuñoa', 'Clínica Andes S.A.', '2026-03-01', '2027-04-30', 'EJECUCION', 1250000000, 'CC-2026-021');
INSERT INTO public.proyectos_proyecto VALUES (4, 'Remodelación Oficinas Providencia', 'Seguros del Pacífico', '2025-08-01', '2026-02-28', 'FINALIZADO', 180000000, 'CC-2025-090');
INSERT INTO public.proyectos_proyecto VALUES (5, 'Bodega Logística Quilicura', 'Logística Norte Ltda', '2027-01-10', NULL, 'PLANIFICACION', 640000000, 'CC-2027-002');
INSERT INTO public.proyectos_proyecto VALUES (3, 'Condominio Piedra Roja – Etapa 2', 'Inmobiliaria Chicureo SpA', '2026-10-02', '2026-10-25', 'EJECUCION', 980000000, 'CC-2026-033');


--
-- Data for Name: usuarios_usuario; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_usuario VALUES (20, 'pbkdf2_sha256$1000000$JWD7T0LvLOvXxY891qx9es$rdlGr2gEzwW/UI3AZKgHTDpPyzklIqOiy4GO+oyUxy8=', '2026-11-14 12:46:51.684952-03', false, 'contador', 'Analista de Contabilidad', '', false, true, '2026-09-07 20:09:12.45619-03', 'contador@m5.cl', '', 'CONTABILIDAD', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (23, '!ULRE9bMmFncjws1oJvlf2jAsTW1QBDLJLxIlXS2x', NULL, false, 'test4', 'test4', 'test4', false, true, '2026-10-04 22:03:32.19265-03', 'test4@gmail.com', '9 8273 3172', 'ENCARGADO_ADQUISICIONES', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (1, 'pbkdf2_sha256$1000000$bz6xNr1AeEzW6aq6PHXHRf$FVp/qlXMwTmqEs/UKBMgRDXzDWZHfNJmhm1cfiAWsl4=', '2026-11-14 19:05:52.989506-03', true, 'admin', 'Administrador General', '', true, true, '2026-06-05 23:31:29.25836-04', 'admin@m5.cl', '', 'ADMIN', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (24, '!ATu39FpMp3m0xku6XLHE2IKF4xefy6QKUyjmrz0J', NULL, false, 'test5', 'test5', 'test5', false, true, '2026-10-04 22:20:06.648922-03', 'test5@gmail.com', '9 7345 9283', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (21, 'pbkdf2_sha256$1000000$u7OLHmtL08BY7BJoqNBox6$UW7b1zOnDxk8JwExUTHHTjWcFOPcTzlVeKK/RkGQ8Ow=', NULL, false, 'tomas.leiva', 'Tomás', 'Leiva', false, false, '2026-10-04 00:30:55.10617-03', 'tomas.leiva@m5.cl', '', 'BODEGUERO', false, true, '');
INSERT INTO public.usuarios_usuario VALUES (7, 'pbkdf2_sha256$720000$ALbZnUewSvjCXnLvufNWYD$J3ICEljUOmQPrgcr5itRr4fhHDD03x5hEvGCyKoTSYk=', NULL, false, 'valentina.soto', 'Valentina', 'Soto', false, true, '2026-09-01 21:16:47.176513-04', 'valentina.soto@m5.cl', '+56 9 8000 0000', 'JEFE_PROYECTO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (8, 'pbkdf2_sha256$720000$2I4SzfVfm7GwxVqRKQhlFQ$vlhBRzjEx05x9u7dZQWj6qfK39ehyzYgJKB8u1bPjhU=', NULL, false, 'ignacio.vega', 'Ignacio', 'Vega', false, true, '2026-09-01 21:16:47.37528-04', 'ignacio.vega@m5.cl', '+56 9 8000 0000', 'ENCARGADO_ADQUISICIONES', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (9, 'pbkdf2_sha256$720000$akLpKnhToQ9ghoKcfWQcJS$KHYcayn5FMNqTTseWktMQibnYxcYoyDspoeUDFh6TtE=', NULL, false, 'paula.herrera', 'Paula', 'Herrera', false, true, '2026-09-01 21:16:47.574004-04', 'paula.herrera@m5.cl', '+56 9 8000 0000', 'ENCARGADO_ADQUISICIONES', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (10, 'pbkdf2_sha256$720000$y8tbqQrd0yibDLueOgsW09$Apk58uhzsaGTfF6OkKOpbqqarj+fE8vxKWrJVBRcSYs=', NULL, false, 'rodrigo.caceres', 'Rodrigo', 'Cáceres', false, true, '2026-09-01 21:16:47.773528-04', 'rodrigo.caceres@m5.cl', '+56 9 8000 0000', 'ENCARGADO_ADQUISICIONES', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (11, 'pbkdf2_sha256$720000$G6D7mo6F4QAvKQOQebz93V$sNgjW5eezaEVknszO048B7DjhjVSZcyrh/K7osfnnzE=', NULL, false, 'fernanda.muñoz', 'Fernanda', 'Muñoz', false, false, '2026-09-01 21:16:47.976485-04', 'fernanda.muñoz@m5.cl', '+56 9 8000 0000', 'ENCARGADO_ADQUISICIONES', false, false, '');
INSERT INTO public.usuarios_usuario VALUES (12, 'pbkdf2_sha256$720000$CiiOlkwXvk6W2vzT4ZBDiN$TYpb9emM08Jn8uaN7Lt3EP2WGBv9XRWvhG4+lMygy6Q=', NULL, false, 'sebastian.araya', 'Sebastián', 'Araya', false, true, '2026-09-01 21:16:48.176065-04', 'sebastian.araya@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (13, 'pbkdf2_sha256$720000$TUCcRe46n3N27tmcfjQaK1$L+sSePFGX571j99Z0+EDzs57dFxxqkKSVvS3MlVd3qE=', NULL, false, 'maria.contreras', 'María', 'Contreras', false, true, '2026-09-01 21:16:48.378467-04', 'maria.contreras@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (16, 'pbkdf2_sha256$720000$cZSoddvHf1iBCapd8d8Lt1$n4AUr1YDM0OEcHAYMvqItP+Qa0HuAVf3g3bngJaRWNM=', NULL, false, 'cristobal.nuñez', 'Cristóbal', 'Núñez', false, true, '2026-09-01 21:16:48.988521-04', 'cristobal.nuñez@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (17, 'pbkdf2_sha256$720000$tYwAax5nDkYCqzSJabbfsU$4ZuEwMSL6thn3ATmZYm+AkZGrybZv6q+gZ+k/E37pNQ=', NULL, false, 'daniela.espinoza', 'Daniela', 'Espinoza', false, true, '2026-09-01 21:16:49.18851-04', 'daniela.espinoza@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (18, 'pbkdf2_sha256$720000$qkPKeJkwJfORKkES6V5LbS$JCv4sXNAooHt0n3MLzzoDK+B4jz8c/S1Fvc3vcRN9oA=', NULL, false, 'matias.torres', 'Matías', 'Torres', false, true, '2026-09-01 21:16:49.392229-04', 'matias.torres@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (19, 'pbkdf2_sha256$720000$qlTNx1WJx68G3zubvdH3w9$jBxaXClx6ox51cvMp1purXQ8GMIhFWgX6jUA3A9JSB8=', NULL, false, 'josefa.salinas', 'Josefa', 'Salinas', false, false, '2026-09-01 21:16:49.595492-04', 'josefa.salinas@m5.cl', '+56 9 8000 0000', 'BODEGUERO', false, false, '');
INSERT INTO public.usuarios_usuario VALUES (22, 'pbkdf2_sha256$1000000$Dp35gYGGgmIVKLEPHScqbi$BtQzZ9CE+HmltjoS6NaGD8j/M9MBz8//08CeFnLHBW8=', NULL, false, 'carla.mendez', 'Carla', 'Méndez', false, false, '2026-10-04 00:30:55.40934-03', 'carla.mendez@m5.cl', '', 'CONTABILIDAD', false, true, '');
INSERT INTO public.usuarios_usuario VALUES (25, '!WqWvjP7eS26iJVlOn4XfzSKl6MwXLz0eFVoLxoqq', NULL, false, 'test6', 'test6', 'test6', false, true, '2026-10-04 22:23:39.739914-03', 'test6@gmail.com', '9 8374 8276', 'JEFE_PROYECTO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (14, 'pbkdf2_sha256$720000$e6Pkc9D3OoWtS7Rr4ZRy4p$zlvKuKhTLNI5yRodXcNO8KGi3mKnIZtrLPaMJl3fdDk=', NULL, false, 'jorge.pizarro', 'Jorge', 'Pizarro', false, true, '2026-09-01 21:16:48.580168-04', 'jorge.pizarro@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (26, '!AJlYZnigdYooAMl4TcbdLYsGYm2LyiYam7deaaYy', NULL, false, 'test7', 'test6', 'test6', false, true, '2026-10-04 22:27:44.986211-03', 'test7@gmail.com', '+569 7347 2734', 'JEFE_PROYECTO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (4, 'pbkdf2_sha256$1000000$EMlSNpw2ZPw7bE3glH1vOP$NT0KALHxweBQyLg7kmHcs8TKcmzqZjtEEzxM+OvF1bM=', '2026-10-04 01:29:27.426369-03', false, 'bodega', 'Bodeguero Turno Mañana', '', false, true, '2026-06-05 23:31:29.856177-04', 'bodega@m5.cl', '', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (27, '!66cxEpVkqC7pm8nhnQzDG1U3XmArVyBVus9uJd4i', NULL, false, 'prueba1', 'prueba1', 'prueba1', false, true, '2026-10-04 22:29:21.364645-03', 'prueba1@gmail.com', '+569 8734 2734', 'JEFE_PROYECTO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (3, 'pbkdf2_sha256$1000000$tnVRtxGFLgQN4WZR9fqmC3$5yl5jzLTosTvnfF2HjYsz7ThJrdlQn1erljcv1oa+5M=', '2026-11-14 19:06:33.607116-03', false, 'encargado', 'Encargado de Adquisiciones', '', false, true, '2026-06-05 23:31:29.660174-04', 'encargado@m5.cl', '', 'ENCARGADO_ADQUISICIONES', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (28, '!dEUAg1aWu7DJEFaMblnQprFcxCvIfDEPrXxtv8Vr', NULL, false, 'prueba2', 'prueba2', 'prueba2', false, true, '2026-10-04 22:37:09.870122-03', 'prueba2@gmail.com', '+569 8934 9283', 'ADMIN', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (5, 'pbkdf2_sha256$720000$ybYY9BQpGEZEfGVRGdoPiI$g87ck3QDPRTrkh9ELMSpbisuBLoOCBFQremhmEFr7cI=', '2026-11-14 12:46:51.666562-03', false, 'camila.rojas', 'Camila', 'Rojas', false, true, '2026-09-01 21:16:46.760987-04', 'camila.rojas@m5.cl', '+56 9 8000 0000', 'JEFE_PROYECTO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (29, '!LLs0yxEviaonSSkP44Y0wwRWW2di0eHd6rddZA34', NULL, false, 'prueba3', 'prueba3', 'prueba3', false, true, '2026-10-04 22:53:41.721986-03', 'prueba3@gmail.com', '+569 8172 9817', 'ADMIN', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (6, 'pbkdf2_sha256$720000$Q57E75LRaSwe1iYUGcxBhx$+67dF5ClLLSLrM3a1cZ+J1eKQ6J8L1vJNl5SHH0373w=', NULL, false, 'diego.fuentes', 'Diego', 'Fuentes', false, true, '2026-09-01 21:16:46.978305-04', 'diego.fuentes@m5.cl', '+56 9 8000 0000', 'JEFE_PROYECTO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (15, 'pbkdf2_sha256$720000$ZyOK782ii7KkHEXAiSVk3J$dLKco8kmaymRZkOiNbDQwOa3sPHvamgj1t4AxY7tmh0=', '2026-11-14 12:46:51.680312-03', false, 'antonia.reyes', 'Antonia', 'Reyes', false, true, '2026-09-01 21:16:48.783878-04', 'antonia.reyes@m5.cl', '+56 9 8000 0000', 'BODEGUERO', true, false, '');
INSERT INTO public.usuarios_usuario VALUES (2, 'pbkdf2_sha256$1000000$72qPEKTg6crWRSpHOD3KtN$HbamCCo0TK3+v3Bh7HK6xRayEDoQxEvQNbvpDljcQ+k=', '2026-11-14 18:25:55.848694-03', false, 'jefe', 'Jefa de Proyecto', '', false, true, '2026-06-05 23:31:29.461153-04', 'jefe@m5.cl', '', 'JEFE_PROYECTO', true, false, '');


--
-- Data for Name: solicitudes_solicitudmaterial; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.solicitudes_solicitudmaterial VALUES (1, 'SM-000001', '2026-06-05 23:31:30.071187-04', 'BORRADOR', 'Materiales para fundaciones del primer nivel.', 3, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (2, 'SM-000002', '2026-06-10 22:01:50.218266-04', 'BORRADOR', 'se solicitan 50 sacos de cemento', 1, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (3, 'SM-000003', '2026-06-10 22:11:07.590813-04', 'BORRADOR', 'esto se necesitara para el miercoles', 1, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (4, 'SM-000004', '2026-06-10 22:15:41.276376-04', 'BORRADOR', 'se necesita para el lunes a primera hora', 1, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (5, 'SM-000005', '2026-06-14 11:06:39.485556-04', 'BORRADOR', 'necitamos 150 clavos para el lunes', 1, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (16, 'SM-000016', '2026-09-27 00:30:55.783448-03', 'OC_GENERADA', 'Fierro para pilares eje C.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (8, 'SM-000008', '2026-09-11 20:24:54.649813-03', 'BORRADOR', '', 1, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (9, 'SM-000009', '2026-10-03 00:30:55.752142-03', 'BORRADOR', 'Terminaciones sala de espera, piso 1.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (12, 'SM-000012', '2026-09-28 00:30:55.761383-03', 'RECHAZADA', 'Compra de EPP para todo el año.', 3, 2, 'Cantidad excesiva; pedir por trimestre.');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (15, 'SM-000015', '2026-09-29 00:30:55.775239-03', 'EN_COTIZACION', 'Moldajes casas tipo B.', 3, 3, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (23, 'SM-000023', '2026-10-04 01:40:01.399506-03', 'BORRADOR', '', 1, 3, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (19, 'SM-000019', '2026-09-14 00:30:55.816266-03', 'RECIBIDA', 'Obra gruesa casas 14 a 20.', 3, 3, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (18, 'SM-000018', '2026-09-24 00:30:55.805995-03', 'OC_GENERADA', 'Áridos para radier acceso.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (17, 'SM-000017', '2026-09-25 00:30:55.798299-03', 'RECEPCION_PARCIAL', 'Pintura fachada norte.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (7, 'SM-000007', '2026-09-07 20:09:12.70581-03', 'OC_GENERADA', 'Compra de cemento y fierro para losa nivel 2.', 3, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (24, 'SM-000024', '2026-10-04 01:41:01.505651-03', 'OC_GENERADA', '', 1, 3, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (20, 'SM-000020', '2026-09-09 00:30:55.842446-03', 'OC_GENERADA', 'Tuberías alcantarillado casas.', 3, 3, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (6, 'SM-000006', '2026-06-16 23:19:22.14552-04', 'EMITIDA', 'necesito 200 clavos para el lunes', 3, 1, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (10, 'SM-000010', '2026-10-02 00:30:55.755737-03', 'EMITIDA', 'Hormigonado muros subterráneo -1.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (13, 'SM-000013', '2026-10-01 00:30:55.763433-03', 'EMITIDA', 'Instalación eléctrica tableros piso 2.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (21, 'SM-000021', '2026-07-05 23:30:55.851167-04', 'RECIBIDA', 'Tabiquería y pintura oficinas piso 8.', 8, 4, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (14, 'SM-000014', '2026-09-30 00:30:55.767032-03', 'EMITIDA', 'Hormigonado losa piso 3.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (22, 'SM-000022', '2026-09-22 00:30:55.869663-03', 'RECIBIDA', 'Cemento de emergencia.', 3, 3, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (11, 'SM-000011', '2026-10-03 00:30:55.75984-03', 'EN_COTIZACION', 'Tabiquería urgente pabellones.', 3, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (25, NULL, '2026-11-14 18:29:38.956351-03', 'BORRADOR', '', 2, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (26, 'SM-000025', '2026-11-14 18:32:08.839642-03', 'OC_GENERADA', '', 2, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (27, 'SM-000026', '2026-11-14 19:14:38.37464-03', 'EN_COTIZACION', '', 2, 2, '');
INSERT INTO public.solicitudes_solicitudmaterial VALUES (28, 'SM-000027', '2026-11-14 19:36:21.474582-03', 'OC_GENERADA', '', 2, 2, '');


--
-- Data for Name: adquisiciones_cotizacion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.adquisiciones_cotizacion VALUES (1, 25000, 3, 'PARCIAL', '2026-09-07 20:09:12.711827-03', 3, 1, 7);
INSERT INTO public.adquisiciones_cotizacion VALUES (2, 18000, 5, 'PARCIAL', '2026-09-07 20:09:12.72057-03', 3, 2, 7);
INSERT INTO public.adquisiciones_cotizacion VALUES (3, 35000, 4, 'PENDIENTE', '2026-10-04 00:30:55.767544-03', 3, 12, 14);
INSERT INTO public.adquisiciones_cotizacion VALUES (4, 60000, 2, 'PENDIENTE', '2026-10-04 00:30:55.771129-03', 3, 3, 14);
INSERT INTO public.adquisiciones_cotizacion VALUES (5, 0, 5, 'PENDIENTE', '2026-10-04 00:30:55.772157-03', 3, 11, 14);
INSERT INTO public.adquisiciones_cotizacion VALUES (6, 45000, 3, 'PARCIAL', '2026-10-04 00:30:55.77575-03', 3, 4, 15);
INSERT INTO public.adquisiciones_cotizacion VALUES (7, 0, 6, 'PENDIENTE', '2026-10-04 00:30:55.779853-03', 3, 11, 15);
INSERT INTO public.adquisiciones_cotizacion VALUES (8, 30000, 3, 'PARCIAL', '2026-10-04 00:30:55.783961-03', 3, 2, 16);
INSERT INTO public.adquisiciones_cotizacion VALUES (9, 15000, 2, 'PARCIAL', '2026-10-04 00:30:55.798812-03', 3, 1, 17);
INSERT INTO public.adquisiciones_cotizacion VALUES (10, 55000, 2, 'PARCIAL', '2026-10-04 00:30:55.806512-03', 3, 3, 18);
INSERT INTO public.adquisiciones_cotizacion VALUES (11, 40000, 3, 'PARCIAL', '2026-10-04 00:30:55.816781-03', 3, 12, 19);
INSERT INTO public.adquisiciones_cotizacion VALUES (12, 25000, 4, 'PARCIAL', '2026-10-04 00:30:55.818829-03', 3, 2, 19);
INSERT INTO public.adquisiciones_cotizacion VALUES (13, 20000, 5, 'PARCIAL', '2026-10-04 00:30:55.84347-03', 3, 9, 20);
INSERT INTO public.adquisiciones_cotizacion VALUES (14, 20000, 2, 'PARCIAL', '2026-10-04 00:30:55.852191-03', 3, 4, 21);
INSERT INTO public.adquisiciones_cotizacion VALUES (15, 0, 3, 'PARCIAL', '2026-10-04 00:30:55.854248-03', 3, 11, 21);
INSERT INTO public.adquisiciones_cotizacion VALUES (16, 0, 1, 'PARCIAL', '2026-10-04 00:30:55.870176-03', 3, 13, 22);
INSERT INTO public.adquisiciones_cotizacion VALUES (17, 0, 1, 'PARCIAL', '2026-11-03 12:11:21.938162-03', 3, 5, 24);
INSERT INTO public.adquisiciones_cotizacion VALUES (18, 0, 1, 'PARCIAL', '2026-11-14 17:40:17.007009-03', 3, 6, 11);
INSERT INTO public.adquisiciones_cotizacion VALUES (19, 15000, 3, 'PARCIAL', '2026-11-14 19:00:40.817517-03', 3, 3, 26);
INSERT INTO public.adquisiciones_cotizacion VALUES (20, 15000, 3, 'PARCIAL', '2026-11-14 19:15:47.153727-03', 3, 3, 27);
INSERT INTO public.adquisiciones_cotizacion VALUES (21, 15000, 3, 'PARCIAL', '2026-11-14 19:38:53.805046-03', 3, 3, 28);


--
-- Data for Name: inventario_material; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.inventario_material VALUES (11, 'Placa de yeso-cartón 15mm', 'plancha', 280.00, 7900, 'CONSUMIBLE', '', NULL, true, 0.00, 'Bodega central · Estante B2', 'OTROS', 'MAT-00010');
INSERT INTO public.inventario_material VALUES (14, 'Disco de corte metal 7"', 'unidad', 375.00, 1990, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00013');
INSERT INTO public.inventario_material VALUES (21, 'Generador eléctrico 3 kVA', 'unidad', 1.00, 349990, 'HERRAMIENTA', 'HER-0006', NULL, true, 0.00, '', 'OTROS', 'HER-00006');
INSERT INTO public.inventario_material VALUES (29, 'Malla acma C-92', 'plancha', 3.00, 27990, 'CONSUMIBLE', '', NULL, true, 10.00, 'Bodega central', 'FIERRO', 'MAT-00021');
INSERT INTO public.inventario_material VALUES (28, 'Casco de seguridad', 'unidad', 4.00, 6990, 'CONSUMIBLE', '', NULL, true, 20.00, 'Bodega central', 'SEGURIDAD', 'MAT-00020');
INSERT INTO public.inventario_material VALUES (15, 'Guantes de seguridad', 'par', 120.00, 2500, 'CONSUMIBLE', '', NULL, true, 150.00, '', 'OTROS', 'MAT-00014');
INSERT INTO public.inventario_material VALUES (2, 'Fierro estriado 12mm', 'barra', 0.00, 8900, 'CONSUMIBLE', '', NULL, true, 200.00, 'Bodega central · Rack fierros', 'OTROS', 'MAT-00002');
INSERT INTO public.inventario_material VALUES (1, 'Cemento Portland 25kg', 'saco', 200.00, 4500, 'CONSUMIBLE', '', NULL, true, 100.00, 'Bodega central · Estante A1', 'OTROS', 'MAT-00001');
INSERT INTO public.inventario_material VALUES (8, 'Arena gruesa', 'm3', 45.00, 18000, 'CONSUMIBLE', '', NULL, true, 40.00, 'Patio exterior', 'OTROS', 'MAT-00007');
INSERT INTO public.inventario_material VALUES (24, 'Moldaje fenólico 18mm', 'plancha', 0.00, 32990, 'CONSUMIBLE', '', NULL, true, 10.00, 'Bodega central', 'MADERA', 'MAT-00016');
INSERT INTO public.inventario_material VALUES (25, 'Pino dimensionado 2x4"', 'pieza', 0.00, 3490, 'CONSUMIBLE', '', NULL, true, 10.00, 'Bodega central', 'MADERA', 'MAT-00017');
INSERT INTO public.inventario_material VALUES (26, 'Cable THHN 2.5mm rollo 100m', 'rollo', 0.00, 45990, 'CONSUMIBLE', '', NULL, true, 10.00, 'Bodega central', 'ELECTRICIDAD', 'MAT-00018');
INSERT INTO public.inventario_material VALUES (27, 'Tubo PVC sanitario 110mm', 'tira', 0.00, 8990, 'CONSUMIBLE', '', NULL, true, 10.00, 'Bodega central', 'GASFITERIA', 'MAT-00019');
INSERT INTO public.inventario_material VALUES (3, 'Taladro percutor', 'unidad', 0.00, 89990, 'HERRAMIENTA', '', NULL, true, 0.00, '', 'OTROS', 'HER-00001');
INSERT INTO public.inventario_material VALUES (4, 'biga', '20 metros', 0.00, 100000, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00003');
INSERT INTO public.inventario_material VALUES (5, 'planchas de metal', '15 metros', 0.00, 0, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00004');
INSERT INTO public.inventario_material VALUES (6, 'Clavos', 'unidad', 0.00, 0, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00005');
INSERT INTO public.inventario_material VALUES (9, 'Gravilla 20mm', 'm3', 38.00, 21000, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00008');
INSERT INTO public.inventario_material VALUES (10, 'Ladrillo fiscal', 'unidad', 9680.00, 380, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00009');
INSERT INTO public.inventario_material VALUES (13, 'Tornillo autoperforante 1"', 'caja', 120.00, 3990, 'CONSUMIBLE', '', NULL, true, 0.00, '', 'OTROS', 'MAT-00012');
INSERT INTO public.inventario_material VALUES (16, 'Cal hidratada 25kg', 'saco', 0.00, 3200, 'CONSUMIBLE', '', NULL, false, 0.00, '', 'OTROS', 'MAT-00015');
INSERT INTO public.inventario_material VALUES (17, 'Esmeril angular 4.5"', 'unidad', 8.00, 45990, 'HERRAMIENTA', 'HER-0002', NULL, true, 0.00, '', 'OTROS', 'HER-00002');
INSERT INTO public.inventario_material VALUES (18, 'Sierra circular 7.1/4"', 'unidad', 5.00, 79990, 'HERRAMIENTA', 'HER-0003', NULL, true, 0.00, '', 'OTROS', 'HER-00003');
INSERT INTO public.inventario_material VALUES (19, 'Martillo demoledor', 'unidad', 3.00, 189990, 'HERRAMIENTA', 'HER-0004', NULL, true, 0.00, '', 'OTROS', 'HER-00004');
INSERT INTO public.inventario_material VALUES (20, 'Nivel láser autonivelante', 'unidad', 4.00, 129990, 'HERRAMIENTA', 'HER-0005', NULL, true, 0.00, '', 'OTROS', 'HER-00005');
INSERT INTO public.inventario_material VALUES (23, 'Betonera 130 lt', 'unidad', 1.00, 259990, 'HERRAMIENTA', 'HER-0008', NULL, false, 0.00, '', 'OTROS', 'HER-00008');
INSERT INTO public.inventario_material VALUES (7, 'Fierro estriado 8mm', 'barra', 285.00, 5200, 'CONSUMIBLE', '', NULL, true, 0.00, 'Bodega central', 'OTROS', 'MAT-00006');
INSERT INTO public.inventario_material VALUES (22, 'Andamio modular (cuerpo)', 'unidad', 40.00, 59990, 'HERRAMIENTA', 'HER-0007', NULL, true, 0.00, '', 'OTROS', 'HER-00007');
INSERT INTO public.inventario_material VALUES (12, 'Pintura látex blanco 1 gal', 'galón', 76.00, 15990, 'CONSUMIBLE', '', NULL, true, 80.00, 'Bodega central · Estante C4', 'OTROS', 'MAT-00011');


--
-- Data for Name: proveedores_proveedormaterial; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.proveedores_proveedormaterial VALUES (3, 'FC-DISCO7', 'Disco de corte metal 7"', 'unidad', false, '2026-09-07 20:09:12.68052-03', '2026-09-07 20:09:12.68052-03', 1, 0, NULL);
INSERT INTO public.proveedores_proveedormaterial VALUES (1, 'FC-CEM25', 'Cemento Portland 25 kg', 'saco', true, '2026-09-07 20:09:12.677521-03', '2026-10-04 00:30:55.72345-03', 1, 4600, 1);
INSERT INTO public.proveedores_proveedormaterial VALUES (2, 'FC-TORN1', 'Tornillo autoperforante 1"', 'caja', true, '2026-09-07 20:09:12.679772-03', '2026-10-04 00:30:55.72396-03', 1, 3800, 13);
INSERT INTO public.proveedores_proveedormaterial VALUES (6, 'FC-GUANT', 'Guantes de seguridad', 'par', true, '2026-10-04 00:30:55.724473-03', '2026-10-04 00:30:55.725499-03', 1, 2400, 15);
INSERT INTO public.proveedores_proveedormaterial VALUES (7, 'FC-CASCO', 'Casco de seguridad', 'unidad', true, '2026-10-04 00:30:55.726524-03', '2026-10-04 00:30:55.726524-03', 1, 7200, 28);
INSERT INTO public.proveedores_proveedormaterial VALUES (8, 'FC-PINT', 'Pintura látex blanco 1 gal', 'galón', true, '2026-10-04 00:30:55.727549-03', '2026-10-04 00:30:55.727549-03', 1, 15500, 12);
INSERT INTO public.proveedores_proveedormaterial VALUES (4, 'AF-F12', 'Fierro estriado 12 mm', 'barra', true, '2026-09-07 20:09:12.68052-03', '2026-10-04 00:30:55.728063-03', 2, 8900, 2);
INSERT INTO public.proveedores_proveedormaterial VALUES (5, 'AF-F8', 'Fierro estriado 8 mm', 'barra', true, '2026-09-07 20:09:12.682779-03', '2026-10-04 00:30:55.728574-03', 2, 5100, 7);
INSERT INTO public.proveedores_proveedormaterial VALUES (9, 'AF-ACMA', 'Malla acma C-92', 'plancha', true, '2026-10-04 00:30:55.729085-03', '2026-10-04 00:30:55.729596-03', 2, 26990, 29);
INSERT INTO public.proveedores_proveedormaterial VALUES (10, 'HB-ARE', 'Arena gruesa', 'm3', true, '2026-10-04 00:30:55.730107-03', '2026-10-04 00:30:55.730107-03', 3, 17500, 8);
INSERT INTO public.proveedores_proveedormaterial VALUES (11, 'HB-GRAV', 'Gravilla 20mm', 'm3', true, '2026-10-04 00:30:55.730622-03', '2026-10-04 00:30:55.731135-03', 3, 20500, 9);
INSERT INTO public.proveedores_proveedormaterial VALUES (12, 'HB-CEM', 'Cemento Portland 25kg', 'saco', true, '2026-10-04 00:30:55.731646-03', '2026-10-04 00:30:55.731646-03', 3, 4700, 1);
INSERT INTO public.proveedores_proveedormaterial VALUES (13, 'MT-FEN18', 'Moldaje fenólico 18mm', 'plancha', true, '2026-10-04 00:30:55.732157-03', '2026-10-04 00:30:55.732675-03', 4, 31990, 24);
INSERT INTO public.proveedores_proveedormaterial VALUES (14, 'MT-P24', 'Pino dimensionado 2x4"', 'pieza', true, '2026-10-04 00:30:55.733186-03', '2026-10-04 00:30:55.733186-03', 4, 3290, 25);
INSERT INTO public.proveedores_proveedormaterial VALUES (15, 'MT-YESO', 'Placa de yeso-cartón 15mm', 'plancha', true, '2026-10-04 00:30:55.733698-03', '2026-10-04 00:30:55.73421-03', 4, 7700, 11);
INSERT INTO public.proveedores_proveedormaterial VALUES (16, 'EA-THHN25', 'Cable THHN 2.5mm rollo 100m', 'rollo', true, '2026-10-04 00:30:55.734722-03', '2026-10-04 00:30:55.734722-03', 6, 44990, 26);
INSERT INTO public.proveedores_proveedormaterial VALUES (17, 'GR-PVC110', 'Tubo PVC sanitario 110mm', 'tira', true, '2026-10-04 00:30:55.735747-03', '2026-10-04 00:30:55.735747-03', 9, 8700, 27);
INSERT INTO public.proveedores_proveedormaterial VALUES (18, 'SD-100234', 'Cemento Portland 25kg', 'saco', true, '2026-10-04 00:30:55.736261-03', '2026-10-04 00:30:55.736775-03', 11, 4890, 1);
INSERT INTO public.proveedores_proveedormaterial VALUES (19, 'SD-200871', 'Ladrillo fiscal', 'unidad', true, '2026-10-04 00:30:55.737286-03', '2026-10-04 00:30:55.737286-03', 11, 410, 10);
INSERT INTO public.proveedores_proveedormaterial VALUES (20, 'SD-301122', 'Placa de yeso-cartón 15mm', 'plancha', true, '2026-10-04 00:30:55.738312-03', '2026-10-04 00:30:55.738312-03', 11, 8190, 11);
INSERT INTO public.proveedores_proveedormaterial VALUES (21, 'SD-401556', 'Pintura látex blanco 1 gal', 'galón', true, '2026-10-04 00:30:55.738824-03', '2026-10-04 00:30:55.739338-03', 11, 16490, 12);
INSERT INTO public.proveedores_proveedormaterial VALUES (22, 'SD-509900', 'Pino dimensionado 2x4"', 'pieza', true, '2026-10-04 00:30:55.739854-03', '2026-10-04 00:30:55.739854-03', 11, 3590, 25);
INSERT INTO public.proveedores_proveedormaterial VALUES (23, 'ML-CEM25', 'Cemento Portland 25kg', 'saco', true, '2026-10-04 00:30:55.740368-03', '2026-10-04 00:30:55.740882-03', 12, 4450, 1);
INSERT INTO public.proveedores_proveedormaterial VALUES (24, 'ML-CAL25', 'Cal hidratada 25kg', 'saco', true, '2026-10-04 00:30:55.741393-03', '2026-10-04 00:30:55.741393-03', 12, 3100, 16);


--
-- Data for Name: proyectos_itemizado; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.proyectos_itemizado VALUES (1, 'OG-01', 'Hormigón armado', 'm3', 1200.00, 300.00, 1);
INSERT INTO public.proyectos_itemizado VALUES (2, 'OG-02', 'Albañilería', 'm2', 800.00, 0.00, 1);
INSERT INTO public.proyectos_itemizado VALUES (3, 'OG-01', 'Excavaciones y fundaciones', 'm3', 900.00, 600.00, 2);
INSERT INTO public.proyectos_itemizado VALUES (4, 'OG-02', 'Hormigón armado estructura', 'm3', 1500.00, 420.00, 2);
INSERT INTO public.proyectos_itemizado VALUES (5, 'OG-03', 'Tabiquería y cielos', 'm2', 3200.00, 150.00, 2);
INSERT INTO public.proyectos_itemizado VALUES (6, 'OG-04', 'Instalaciones eléctricas', 'gl', 1.00, 0.00, 2);
INSERT INTO public.proyectos_itemizado VALUES (7, 'OG-05', 'Pinturas y terminaciones', 'm2', 5000.00, 0.00, 2);
INSERT INTO public.proyectos_itemizado VALUES (8, 'OG-01', 'Obra gruesa casas', 'm3', 700.00, 380.00, 3);
INSERT INTO public.proyectos_itemizado VALUES (9, 'OG-02', 'Moldajes', 'm2', 2400.00, 900.00, 3);
INSERT INTO public.proyectos_itemizado VALUES (10, 'OG-03', 'Instalaciones sanitarias', 'ml', 1800.00, 300.00, 3);
INSERT INTO public.proyectos_itemizado VALUES (11, 'TE-01', 'Tabiquería yeso-cartón', 'm2', 900.00, 900.00, 4);
INSERT INTO public.proyectos_itemizado VALUES (12, 'TE-02', 'Pintura interior', 'm2', 2500.00, 2500.00, 4);
INSERT INTO public.proyectos_itemizado VALUES (13, 'OG-01', 'Radier industrial', 'm2', 6000.00, 0.00, 5);


--
-- Data for Name: solicitudes_solicituddetalle; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.solicitudes_solicituddetalle VALUES (1, 200.00, 'saco', 1, 1, NULL, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (2, 150.00, 'barra', 2, 1, NULL, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (3, 15.00, '20 metros', 4, 3, NULL, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (4, 10.00, '15 metros', 5, 4, NULL, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (5, 150.00, 'unidad', 6, 5, NULL, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (6, 200.00, 'unidad', 6, 6, NULL, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (7, 120.00, 'saco', 1, 7, 1, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (8, 80.00, 'barra', 2, 7, 1, '', '', NULL, NULL, 0);
INSERT INTO public.solicitudes_solicituddetalle VALUES (9, 3.00, 'caja', 13, 8, NULL, '', '', 1, 2, 1000);
INSERT INTO public.solicitudes_solicituddetalle VALUES (10, 3.00, 'unidad', 10, 8, NULL, '', '', 8, NULL, 500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (11, 40.00, 'galón', 12, 9, 7, '', '', 11, 21, 16490);
INSERT INTO public.solicitudes_solicituddetalle VALUES (12, 120.00, 'plancha', 11, 9, 5, '', '', 4, 15, 7700);
INSERT INTO public.solicitudes_solicituddetalle VALUES (13, 400.00, 'saco', 1, 10, 4, '', '', 12, 23, 4450);
INSERT INTO public.solicitudes_solicituddetalle VALUES (14, 250.00, 'barra', 2, 10, 4, '', '', 2, 4, 8900);
INSERT INTO public.solicitudes_solicituddetalle VALUES (15, 60.00, 'plancha', 29, 10, 3, '', '', 2, 9, 26990);
INSERT INTO public.solicitudes_solicituddetalle VALUES (16, 3500.00, 'plancha', 11, 11, 5, 'El itemizado no consideró el cambio de layout de pabellones (ORD-14).', '', 11, 20, 8190);
INSERT INTO public.solicitudes_solicituddetalle VALUES (17, 2000.00, 'par', 15, 12, NULL, '', '', 1, 6, 2400);
INSERT INTO public.solicitudes_solicituddetalle VALUES (18, 35.00, 'rollo', 26, 13, NULL, '', '', 6, 16, 44990);
INSERT INTO public.solicitudes_solicituddetalle VALUES (19, 50.00, 'par', 15, 13, NULL, '', '', NULL, NULL, 2500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (20, 300.00, 'saco', 1, 14, 4, '', '', 12, 23, 4450);
INSERT INTO public.solicitudes_solicituddetalle VALUES (21, 25.00, 'm3', 8, 14, 4, '', '', 3, 10, 17500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (22, 30.00, 'm3', 9, 14, 4, '', '', 3, 11, 20500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (23, 80.00, 'plancha', 24, 15, 9, '', '', 4, 13, 31990);
INSERT INTO public.solicitudes_solicituddetalle VALUES (24, 400.00, 'pieza', 25, 15, 9, '', '', 4, 14, 3290);
INSERT INTO public.solicitudes_solicituddetalle VALUES (25, 180.00, 'barra', 2, 16, 4, '', '', 2, 4, 8900);
INSERT INTO public.solicitudes_solicituddetalle VALUES (26, 220.00, 'barra', 7, 16, 4, '', '', 2, 5, 5100);
INSERT INTO public.solicitudes_solicituddetalle VALUES (27, 90.00, 'galón', 12, 17, 7, '', '', 1, 8, 15500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (28, 20.00, 'm3', 8, 18, 3, '', '', 3, 10, 17500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (29, 18.00, 'm3', 9, 18, 3, '', '', 3, 11, 20500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (30, 250.00, 'saco', 1, 19, 8, '', '', 12, 23, 4450);
INSERT INTO public.solicitudes_solicituddetalle VALUES (31, 40.00, 'plancha', 29, 19, 8, '', '', 2, 9, 26990);
INSERT INTO public.solicitudes_solicituddetalle VALUES (32, 150.00, 'barra', 7, 19, 8, '', '', 2, 5, 5100);
INSERT INTO public.solicitudes_solicituddetalle VALUES (33, 120.00, 'tira', 27, 20, 10, '', '', 9, 17, 8700);
INSERT INTO public.solicitudes_solicituddetalle VALUES (34, 300.00, 'plancha', 11, 21, 11, '', '', 4, 15, 7700);
INSERT INTO public.solicitudes_solicituddetalle VALUES (35, 120.00, 'galón', 12, 21, 12, '', '', 11, 21, 16490);
INSERT INTO public.solicitudes_solicituddetalle VALUES (36, 60.00, 'saco', 1, 22, 8, '', '', NULL, NULL, 4500);
INSERT INTO public.solicitudes_solicituddetalle VALUES (37, 10.00, 'unidad', 28, 23, NULL, '', '', 1, 7, 7200);
INSERT INTO public.solicitudes_solicituddetalle VALUES (38, 10.00, 'unidad', 28, 24, 10, '', '', 1, 7, 7200);
INSERT INTO public.solicitudes_solicituddetalle VALUES (39, 12.00, 'plancha', 11, 23, NULL, '', '', 4, 15, 7700);
INSERT INTO public.solicitudes_solicituddetalle VALUES (40, 50.00, 'saco', 1, 25, 3, '', '', 12, 23, 4450);
INSERT INTO public.solicitudes_solicituddetalle VALUES (41, 50.00, 'saco', 1, 26, 3, '', '', 3, 12, 4450);
INSERT INTO public.solicitudes_solicituddetalle VALUES (42, 30.00, 'saco', 1, 27, 3, '', '', 3, 12, 4700);
INSERT INTO public.solicitudes_solicituddetalle VALUES (43, 40.00, 'saco', 1, 28, 3, '', '', 1, 1, 4600);


--
-- Data for Name: adquisiciones_cotizacionlinea; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.adquisiciones_cotizacionlinea VALUES (3, 4750, 'DESCARTADA', 2, 7);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (1, 4600, 'APROBADA', 1, 7);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (2, 9200, 'DESCARTADA', 1, 8);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (4, 8900, 'APROBADA', 2, 8);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (5, 4450, 'PENDIENTE', 3, 20);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (6, 4700, 'PENDIENTE', 4, 20);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (7, 17500, 'PENDIENTE', 4, 21);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (8, 20500, 'PENDIENTE', 4, 22);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (9, 4890, 'PENDIENTE', 5, 20);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (10, 31990, 'APROBADA', 6, 23);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (11, 3290, 'APROBADA', 6, 24);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (12, 3590, 'PENDIENTE', 7, 24);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (13, 8900, 'APROBADA', 8, 25);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (14, 5100, 'APROBADA', 8, 26);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (15, 15500, 'APROBADA', 9, 27);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (16, 17500, 'APROBADA', 10, 28);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (17, 20500, 'APROBADA', 10, 29);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (18, 4450, 'APROBADA', 11, 30);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (19, 26990, 'APROBADA', 12, 31);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (20, 5100, 'APROBADA', 12, 32);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (21, 8700, 'APROBADA', 13, 33);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (22, 7700, 'APROBADA', 14, 34);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (23, 16490, 'APROBADA', 15, 35);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (24, 4990, 'APROBADA', 16, 36);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (25, 10000, 'APROBADA', 17, 38);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (26, 3500, 'APROBADA', 18, 16);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (27, 4450, 'APROBADA', 19, 41);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (28, 4500, 'APROBADA', 20, 42);
INSERT INTO public.adquisiciones_cotizacionlinea VALUES (29, 4450, 'APROBADA', 21, 43);


--
-- Data for Name: adquisiciones_ordencompra; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.adquisiciones_ordencompra VALUES (18, '13285', 15000, 'BORRADOR', false, '', '76.543.210-3', 'Hormigones Bío-Bío S.A.', '30 días', '2026-11-14 19:40:00.62734-03', NULL, NULL, NULL, 21, 3, 3, 28, 2, 13285, false, 'Av. Pedro de Valdivia 1200, Concepción');
INSERT INTO public.adquisiciones_ordencompra VALUES (3, 'OC-000003', 30000, 'ENVIADA', false, '', '12.345.678-5', 'Aceros y Fierros del Sur Ltda', '60 días', '2026-10-02 00:30:55.796247-03', '2026-10-04 01:56:07.687498-03', '2026-10-04 01:56:07.733492-03', 1, 8, 3, 2, 16, 2, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (5, 'OC-000005', 55000, 'ENVIADA', false, '', '76.543.210-9', 'Hormigones Bío-Bío S.A.', '30 días', '2026-10-01 00:30:55.812147-03', '2026-10-02 00:30:55.812147-03', '2026-10-02 00:30:55.812147-03', 2, 10, 3, 3, 18, 2, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (4, 'OC-000004', 15000, 'RECEPCION_PARCIAL', false, '', '11.111.111-1', 'Ferretería El Constructor SpA', '30 días', '2026-09-30 00:30:55.802916-03', '2026-10-04 02:03:19.118729-03', '2026-10-04 02:03:19.17185-03', 1, 9, 3, 1, 17, 2, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (11, 'OC-000011', 0, 'RECIBIDA', false, '', '77.111.222-6', 'Ferretería Sin Correo Ltda', 'Contado', '2026-09-24 00:30:55.874283-03', '2026-09-25 00:30:55.874283-03', '2026-09-25 00:30:55.874283-03', 5, 16, 3, 13, 22, 3, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (7, 'OC-000007', 25000, 'RECIBIDA', true, '', '12.345.678-5', 'Aceros y Fierros del Sur Ltda', '60 días', '2026-09-19 00:30:55.826534-03', '2026-09-20 00:30:55.826534-03', '2026-09-20 00:30:55.826534-03', 5, 12, 3, 2, 19, 3, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (6, 'OC-000006', 40000, 'RECIBIDA', true, '', '93.248.000-K', 'Cementos Melón S.A.', '60 días', '2026-09-19 00:30:55.825503-03', '2026-09-20 00:30:55.825503-03', '2026-09-20 00:30:55.825503-03', 5, 11, 3, 12, 19, 3, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (8, 'OC-000008', 20000, 'NO_RECIBIDA', false, '', '78.567.890-6', 'Gasfitería y Riego Aconcagua', '30 días', '2026-09-14 00:30:55.847573-03', '2026-09-15 00:30:55.847573-03', '2026-09-15 00:30:55.847573-03', 5, 13, 3, 9, 20, 3, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (2, 'OC-000002', 18000, 'ENVIADA', false, '', '12.345.678-5', 'Aceros y Fierros del Sur Ltda', '60 días', '2026-09-07 20:09:12.734168-03', '2026-10-04 02:07:16.761534-03', '2026-10-04 02:07:16.796248-03', 1, 2, 3, 2, 7, 1, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (1, 'OC-000001', 25000, 'RECEPCION_PARCIAL', true, '', '11.111.111-1', 'Ferretería El Constructor SpA', '30 días', '2026-09-07 20:09:12.730909-03', '2026-09-07 20:09:12.737583-03', '2026-09-07 20:09:12.737583-03', 2, 1, 3, 1, 7, 1, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (10, 'OC-000010', 0, 'RECIBIDA', true, '', '96.792.430-K', 'Sodimac Empresas S.A.', '30 días', '2026-07-10 23:30:55.860417-04', '2026-07-11 23:30:55.860417-04', '2026-07-11 23:30:55.860417-04', 6, 15, 3, 11, 21, 4, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (9, 'OC-000009', 20000, 'RECIBIDA', true, '', '77.888.999-8', 'Maderas y Terciados Pucón Ltda', 'Contado', '2026-07-10 23:30:55.859392-04', '2026-07-11 23:30:55.859907-04', '2026-07-11 23:30:55.859907-04', 6, 14, 3, 4, 21, 4, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (12, 'OC-000012', 0, 'ENVIADA', false, '', '78.123.456-7', 'Áridos y Transportes Maipo SpA', '90 días', '2026-11-03 12:11:30.399509-03', '2026-11-09 20:41:18.526959-03', '2026-11-09 20:41:19.007668-03', 1, 17, 3, 5, 24, 3, NULL, false, '');
INSERT INTO public.adquisiciones_ordencompra VALUES (17, '1', 15000, 'BORRADOR', false, '', '76.543.210-3', 'Hormigones Bío-Bío S.A.', '30 días', '2026-11-14 19:08:37.635145-03', NULL, NULL, NULL, 19, 3, 3, 26, 2, 1, false, 'Av. Pedro de Valdivia 1200, Concepción');


--
-- Data for Name: adquisiciones_ordencompralinea; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.adquisiciones_ordencompralinea VALUES (2, 'Fierro estriado 12 mm', 80.00, 'barra', 8900, 0.00, 2, 2);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (1, 'Cemento Portland 25 kg', 120.00, 'saco', 4600, 80.00, 1, 1);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (3, 'Fierro estriado 12mm', 180.00, 'barra', 8900, 0.00, 2, 3);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (4, 'Fierro estriado 8mm', 220.00, 'barra', 5100, 0.00, 7, 3);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (6, 'Arena gruesa', 20.00, 'm3', 17500, 0.00, 8, 5);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (7, 'Gravilla 20mm', 18.00, 'm3', 20500, 0.00, 9, 5);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (8, 'Cemento Portland 25kg', 250.00, 'saco', 4450, 250.00, 1, 6);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (9, 'Malla acma C-92', 40.00, 'plancha', 26990, 20.00, 29, 7);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (10, 'Fierro estriado 8mm', 150.00, 'barra', 5100, 75.00, 7, 7);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (11, 'Tubo PVC sanitario 110mm', 120.00, 'tira', 8700, 0.00, 27, 8);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (12, 'Placa de yeso-cartón 15mm', 300.00, 'plancha', 7700, 300.00, 11, 9);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (13, 'Pintura látex blanco 1 gal', 120.00, 'galón', 16490, 120.00, 12, 10);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (14, 'Cemento Portland 25kg', 60.00, 'saco', 4990, 60.00, 1, 11);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (5, 'Pintura látex blanco 1 gal', 90.00, 'galón', 15500, 1.00, 12, 4);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (15, 'Casco de seguridad', 10.00, 'unidad', 10000, 0.00, 28, 12);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (20, 'Cemento Portland 25kg', 50.00, 'saco', 4450, 0.00, 1, 17);
INSERT INTO public.adquisiciones_ordencompralinea VALUES (21, 'Cemento Portland 25kg', 40.00, 'saco', 4450, 0.00, 1, 18);


--
-- Data for Name: auditoria_registroauditoria; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.auditoria_registroauditoria VALUES (104, 'Jefa de Proyecto', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (1 ítem(s)).', 'SM-000025', '2026-11-14 18:43:18.462486-03', 2, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (108, 'Jefa de Proyecto', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (1 ítem(s)).', 'SM-000027', '2026-11-14 19:37:35.674725-03', 2, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (105, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Hormigones Bío-Bío S.A. por la solicitud SM-000025.', '1', '2026-11-14 19:08:37.636916-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (109, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Hormigones Bío-Bío S.A. por la solicitud SM-000027.', '13285', '2026-11-14 19:40:00.628848-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (46, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 300 plancha de Placa de yeso-cartón 15mm.', 'Placa de yeso-cartón 15mm', '2026-10-04 00:30:55.861957-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (106, 'Encargado de Adquisiciones', 'PARAMETROS_MODIFICADOS', 'CONFIGURACION', 'Cambió el próximo folio de OC de 2 a 13285.', 'Folio OC', '2026-11-14 19:11:07.997298-03', 3, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (30, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 250 saco de Cemento Portland 25kg.', 'Cemento Portland 25kg', '2026-10-04 00:30:55.83114-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (31, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 20 plancha de Malla acma C-92.', 'Malla acma C-92', '2026-10-04 00:30:55.83525-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (32, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 75 barra de Fierro estriado 8mm.', 'Fierro estriado 8mm', '2026-10-04 00:30:55.83833-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (47, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 120 galón de Pintura látex blanco 1 gal.', 'Pintura látex blanco 1 gal', '2026-10-04 00:30:55.865559-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (53, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 60 saco de Cemento Portland 25kg.', 'Cemento Portland 25kg', '2026-10-04 00:30:55.87582-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (54, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Salida a obra de 150 saco de Cemento Portland 25kg.', 'Cemento Portland 25kg', '2026-10-04 00:30:55.878389-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (55, 'Sebastián Araya', 'MOV_INVENTARIO', 'INVENTARIO', 'Salida a obra de 15 plancha de Malla acma C-92.', 'Malla acma C-92', '2026-10-04 00:30:55.879413-03', 12, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (56, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Salida a obra de 290 plancha de Placa de yeso-cartón 15mm.', 'Placa de yeso-cartón 15mm', '2026-10-04 00:30:55.879926-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (57, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Salida a obra de 115 galón de Pintura látex blanco 1 gal.', 'Pintura látex blanco 1 gal', '2026-10-04 00:30:55.880438-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (59, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Salida a obra de 60 par de Guantes de seguridad.', 'Guantes de seguridad', '2026-10-04 00:30:55.881981-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (60, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 10 plancha de Placa de yeso-cartón 15mm.', 'Placa de yeso-cartón 15mm', '2026-10-04 00:30:55.883008-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (61, 'Sebastián Araya', 'MOV_INVENTARIO', 'INVENTARIO', 'Merma / pérdida de 25 unidad de Disco de corte metal 7".', 'Disco de corte metal 7"', '2026-10-04 00:30:55.883522-03', 12, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (62, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Merma / pérdida de 8 saco de Cemento Portland 25kg.', 'Cemento Portland 25kg', '2026-10-04 00:30:55.884549-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (63, 'Bodeguero Turno Mañana', 'MOV_INVENTARIO', 'INVENTARIO', 'Devolución a proveedor de 2 plancha de Malla acma C-92.', 'Malla acma C-92', '2026-10-04 00:30:55.885061-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (87, 'Administrador General', 'MOV_INVENTARIO', 'INVENTARIO', 'Entrada a bodega de 1 galón de Pintura látex blanco 1 gal.', 'Pintura látex blanco 1 gal', '2026-10-04 02:03:43.346793-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (88, 'Administrador General', 'MOV_INVENTARIO', 'INVENTARIO', 'Salida a obra de 1 saco de Cemento Portland 25kg.', 'Cemento Portland 25kg', '2026-10-04 02:04:20.957639-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (90, 'Administrador General', 'MOV_INVENTARIO', 'INVENTARIO', 'Merma / pérdida de 1 saco de Cemento Portland 25kg.', 'Cemento Portland 25kg', '2026-10-04 02:06:04.839055-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (64, 'Bodeguero Turno Mañana', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Prestó Esmeril angular 4.5" a Camila Rojas.', 'HER-0002', '2026-10-04 00:30:55.889163-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (65, 'Bodeguero Turno Mañana', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Prestó Nivel láser autonivelante a Jefa de Proyecto.', 'HER-0005', '2026-10-04 00:30:55.889163-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (66, 'Bodeguero Turno Mañana', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Prestó Sierra circular 7.1/4" a Diego Fuentes.', 'HER-0003', '2026-10-04 00:30:55.889679-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (68, 'Bodeguero Turno Mañana', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Prestó Generador eléctrico 3 kVA a Camila Rojas.', 'HER-0006', '2026-10-04 00:30:55.890708-03', 4, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (89, 'Administrador General', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Prestó Generador eléctrico 3 kVA a Camila Rojas.', 'HER-0006', '2026-10-04 02:05:32.912958-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (1, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (3 ítems).', 'SM-000010', '2026-10-04 00:30:55.756249-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (2, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (1 ítems).', 'SM-000011', '2026-10-04 00:30:55.760354-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (3, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (1 ítems).', 'SM-000012', '2026-10-04 00:30:55.761894-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (5, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (2 ítems).', 'SM-000013', '2026-10-04 00:30:55.763433-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (7, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (3 ítems).', 'SM-000014', '2026-10-04 00:30:55.767544-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (9, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Condominio Piedra Roja – Etapa 2 (2 ítems).', 'SM-000015', '2026-10-04 00:30:55.77575-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (11, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (2 ítems).', 'SM-000016', '2026-10-04 00:30:55.783448-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (14, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (1 ítems).', 'SM-000017', '2026-10-04 00:30:55.798299-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (17, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (2 ítems).', 'SM-000018', '2026-10-04 00:30:55.805995-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (22, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Condominio Piedra Roja – Etapa 2 (3 ítems).', 'SM-000019', '2026-10-04 00:30:55.816266-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (33, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Condominio Piedra Roja – Etapa 2 (1 ítems).', 'SM-000020', '2026-10-04 00:30:55.842956-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (38, 'Ignacio Vega', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Remodelación Oficinas Providencia (2 ítems).', 'SM-000021', '2026-10-04 00:30:55.851679-03', 8, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (48, 'Encargado de Adquisiciones', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Condominio Piedra Roja – Etapa 2 (1 ítems).', 'SM-000022', '2026-10-04 00:30:55.869663-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (80, 'Administrador General', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Condominio Piedra Roja – Etapa 2 (1 ítem(s)).', 'SM-000024', '2026-10-04 01:54:54.913825-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (83, 'Administrador General', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Condominio Piedra Roja – Etapa 2 (2 ítem(s)).', 'SM-000023', '2026-10-04 01:58:07.265644-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (6, 'Jefa de Proyecto', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Centro Médico Ñuñoa.', 'SM-000013', '2026-10-04 00:30:55.763945-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (8, 'Jefa de Proyecto', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Centro Médico Ñuñoa.', 'SM-000014', '2026-10-04 00:30:55.767544-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (10, 'Camila Rojas', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Condominio Piedra Roja – Etapa 2.', 'SM-000015', '2026-10-04 00:30:55.77575-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (12, 'Jefa de Proyecto', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Centro Médico Ñuñoa.', 'SM-000016', '2026-10-04 00:30:55.783961-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (15, 'Jefa de Proyecto', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Centro Médico Ñuñoa.', 'SM-000017', '2026-10-04 00:30:55.798299-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (18, 'Jefa de Proyecto', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Centro Médico Ñuñoa.', 'SM-000018', '2026-10-04 00:30:55.806512-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (23, 'Camila Rojas', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Condominio Piedra Roja – Etapa 2.', 'SM-000019', '2026-10-04 00:30:55.816781-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (34, 'Camila Rojas', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Condominio Piedra Roja – Etapa 2.', 'SM-000020', '2026-10-04 00:30:55.842956-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (39, 'Diego Fuentes', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Remodelación Oficinas Providencia.', 'SM-000021', '2026-10-04 00:30:55.851679-03', 6, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (49, 'Camila Rojas', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Condominio Piedra Roja – Etapa 2.', 'SM-000022', '2026-10-04 00:30:55.870176-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (77, 'Administrador General', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Centro Médico Ñuñoa.', 'SM-000011', '2026-10-04 00:58:52.919591-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (100, 'Encargado de Adquisiciones', 'SM_APROBADA', 'SOLICITUDES', 'Aprobó la solicitud de Condominio Piedra Roja – Etapa 2.', 'SM-000024', '2026-11-03 12:10:47.196102-03', 3, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (4, 'Jefa de Proyecto', 'SM_RECHAZADA', 'SOLICITUDES', 'Rechazó la solicitud: Cantidad excesiva; pedir por trimestre.', 'SM-000012', '2026-10-04 00:30:55.761894-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (84, 'Administrador General', 'SM_RECHAZADA', 'SOLICITUDES', 'Rechazó la solicitud de Condominio Piedra Roja – Etapa 2: demasiados materiales', 'SM-000023', '2026-10-04 01:59:05.110649-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (13, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Aceros y Fierros del Sur Ltda por la solicitud SM-000016.', 'OC-000003', '2026-10-04 00:30:55.795736-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (16, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Ferretería El Constructor SpA por la solicitud SM-000017.', 'OC-000004', '2026-10-04 00:30:55.802406-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (19, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Hormigones Bío-Bío S.A. por la solicitud SM-000018.', 'OC-000005', '2026-10-04 00:30:55.811633-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (24, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Cementos Melón S.A. por la solicitud SM-000019.', 'OC-000006', '2026-10-04 00:30:55.823966-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (25, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Aceros y Fierros del Sur Ltda por la solicitud SM-000019.', 'OC-000007', '2026-10-04 00:30:55.824991-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (35, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Gasfitería y Riego Aconcagua por la solicitud SM-000020.', 'OC-000008', '2026-10-04 00:30:55.847058-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (40, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Maderas y Terciados Pucón Ltda por la solicitud SM-000021.', 'OC-000009', '2026-10-04 00:30:55.857851-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (41, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Sodimac Empresas S.A. por la solicitud SM-000021.', 'OC-000010', '2026-10-04 00:30:55.858875-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (50, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Ferretería Sin Correo Ltda por la solicitud SM-000022.', 'OC-000011', '2026-10-04 00:30:55.873771-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (101, 'Encargado de Adquisiciones', 'OC_EMITIDA', 'ADQUISICIONES', 'Emitió la orden de compra a Áridos y Transportes Maipo SpA por la solicitud SM-000024.', 'OC-000012', '2026-11-03 12:11:30.41037-03', 3, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (20, 'Jefa de Proyecto', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Hormigones Bío-Bío S.A..', 'OC-000005', '2026-10-04 00:30:55.812662-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (26, 'Camila Rojas', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Cementos Melón S.A..', 'OC-000006', '2026-10-04 00:30:55.82602-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (28, 'Camila Rojas', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Aceros y Fierros del Sur Ltda.', 'OC-000007', '2026-10-04 00:30:55.827049-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (36, 'Camila Rojas', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Gasfitería y Riego Aconcagua.', 'OC-000008', '2026-10-04 00:30:55.848088-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (42, 'Diego Fuentes', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Maderas y Terciados Pucón Ltda.', 'OC-000009', '2026-10-04 00:30:55.859907-03', 6, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (44, 'Diego Fuentes', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Sodimac Empresas S.A..', 'OC-000010', '2026-10-04 00:30:55.860931-03', 6, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (51, 'Camila Rojas', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Ferretería Sin Correo Ltda.', 'OC-000011', '2026-10-04 00:30:55.874795-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (81, 'Administrador General', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Aceros y Fierros del Sur Ltda.', 'OC-000003', '2026-10-04 01:56:07.696188-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (85, 'Administrador General', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Ferretería El Constructor SpA.', 'OC-000004', '2026-10-04 02:03:19.131486-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (91, 'Administrador General', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Aceros y Fierros del Sur Ltda.', 'OC-000002', '2026-10-04 02:07:16.765112-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (102, 'Administrador General', 'OC_APROBADA', 'ADQUISICIONES', 'Aprobó la orden de compra a Áridos y Transportes Maipo SpA.', 'OC-000012', '2026-11-09 20:41:18.532724-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (21, 'Jefa de Proyecto', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Hormigones Bío-Bío S.A. (contacto@hormigones.cl).', 'OC-000005', '2026-10-04 00:30:55.812662-03', 2, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (27, 'Camila Rojas', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Cementos Melón S.A. (ventas@melon.cl).', 'OC-000006', '2026-10-04 00:30:55.826534-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (29, 'Camila Rojas', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Aceros y Fierros del Sur Ltda (contacto@aceros.cl).', 'OC-000007', '2026-10-04 00:30:55.827049-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (37, 'Camila Rojas', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Gasfitería y Riego Aconcagua (contacto@gasfiteria.cl).', 'OC-000008', '2026-10-04 00:30:55.848088-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (43, 'Diego Fuentes', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Maderas y Terciados Pucón Ltda (contacto@maderas.cl).', 'OC-000009', '2026-10-04 00:30:55.859907-03', 6, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (45, 'Diego Fuentes', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Sodimac Empresas S.A. (empresas@sodimac.cl).', 'OC-000010', '2026-10-04 00:30:55.860931-03', 6, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (52, 'Camila Rojas', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Ferretería Sin Correo Ltda (sin correo).', 'OC-000011', '2026-10-04 00:30:55.874795-03', 5, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (82, 'Administrador General', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Aceros y Fierros del Sur Ltda (contacto@aceros.cl).', 'OC-000003', '2026-10-04 01:56:08.994659-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (86, 'Administrador General', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Ferretería El Constructor SpA (contacto@ferreteria.cl).', 'OC-000004', '2026-10-04 02:03:19.176974-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (92, 'Administrador General', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Aceros y Fierros del Sur Ltda (contacto@aceros.cl).', 'OC-000002', '2026-10-04 02:07:16.802929-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (103, 'Administrador General', 'OC_ENVIADA', 'ADQUISICIONES', 'Envió la orden de compra a Áridos y Transportes Maipo SpA (contacto@aridos.cl).', 'OC-000012', '2026-11-09 20:41:20.287833-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (70, 'Analista de Contabilidad', 'FACTURA_RECIBIDA', 'FACTURACION', 'Recibió la factura de Maderas y Terciados Pucón Ltda por $2.330.000.', '33415', '2026-10-04 00:30:55.897885-03', 20, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (71, 'Analista de Contabilidad', 'FACTURA_RECIBIDA', 'FACTURACION', 'Recibió la factura de Sodimac Empresas S.A. por $2.137.104.', '118902', '2026-10-04 00:30:55.899421-03', 20, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (74, 'Analista de Contabilidad', 'FACTURA_RECIBIDA', 'FACTURACION', 'Recibió la factura de Cementos Melón S.A. por $1.152.500.', '7781', '2026-10-04 00:30:55.9025-03', 20, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (75, 'Analista de Contabilidad', 'FACTURA_RECIBIDA', 'FACTURACION', 'Recibió la factura de Aceros y Fierros del Sur Ltda por $2.093.952.', 'A-5520', '2026-10-04 00:30:55.904038-03', 20, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (72, 'Analista de Contabilidad', 'FACTURA_BLOQUEADA', 'FACTURACION', 'Factura bloqueada: 8.00% de diferencia con las OC.', '118902', '2026-10-04 00:30:55.899934-03', 20, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (76, 'Analista de Contabilidad', 'FACTURA_BLOQUEADA', 'FACTURACION', 'Factura bloqueada: 12.00% de diferencia con las OC.', 'A-5520', '2026-10-04 00:30:55.904038-03', 20, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (73, 'Administrador General', 'FACTURA_DESBLOQUEADA', 'FACTURACION', 'Desbloqueó la factura: flete adicional acordado.', '118902', '2026-10-04 00:30:55.900445-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (93, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de test4 (Encargado de Adquisiciones).', 'test4', '2026-10-04 22:03:32.227037-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (94, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de test5 (Bodeguero).', 'test5', '2026-10-04 22:20:06.653141-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (95, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de test6 (Jefe de Proyecto).', 'test6', '2026-10-04 22:23:39.745383-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (96, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de test7 (Jefe de Proyecto).', 'test7', '2026-10-04 22:27:44.990488-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (97, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de prueba1 (Jefe de Proyecto).', 'prueba1', '2026-10-04 22:29:21.368418-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (98, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de prueba2 (Administrador).', 'prueba2', '2026-10-04 22:37:09.875225-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (99, 'Administrador General', 'USUARIO_CREADO', 'Usuarios', 'Creó la cuenta de prueba3 (Administrador).', 'prueba3', '2026-10-04 22:53:41.727763-03', 1, 'CREAR');
INSERT INTO public.auditoria_registroauditoria VALUES (78, 'Administrador General', 'USUARIO_MODIFICADO', 'Usuarios', 'Cuenta de diego.fuentes inactivada.', 'diego.fuentes', '2026-10-04 01:49:42.61026-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (79, 'Administrador General', 'USUARIO_MODIFICADO', 'Usuarios', 'Cuenta de diego.fuentes activada.', 'diego.fuentes', '2026-10-04 01:50:01.463128-03', 1, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (67, 'Bodeguero Turno Mañana', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Recibió la devolución de Sierra circular 7.1/4".', 'HER-0003', '2026-10-04 00:30:55.890708-03', 4, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (69, 'Bodeguero Turno Mañana', 'PRESTAMO_HERRAMIENTA', 'INVENTARIO', 'Recibió la devolución de Generador eléctrico 3 kVA.', 'HER-0006', '2026-10-04 00:30:55.89122-03', 4, 'EDITAR');
INSERT INTO public.auditoria_registroauditoria VALUES (107, 'Jefa de Proyecto', 'SM_EMITIDA', 'SOLICITUDES', 'Emitió la solicitud de material para Centro Médico Ñuñoa (1 ítem(s)).', 'SM-000026', '2026-11-14 19:14:55.150221-03', 2, 'CREAR');


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_content_type VALUES (1, 'admin', 'logentry');
INSERT INTO public.django_content_type VALUES (2, 'auth', 'permission');
INSERT INTO public.django_content_type VALUES (3, 'auth', 'group');
INSERT INTO public.django_content_type VALUES (4, 'contenttypes', 'contenttype');
INSERT INTO public.django_content_type VALUES (5, 'sessions', 'session');
INSERT INTO public.django_content_type VALUES (6, 'usuarios', 'usuario');
INSERT INTO public.django_content_type VALUES (7, 'usuarios', 'perfilbodeguero');
INSERT INTO public.django_content_type VALUES (8, 'usuarios', 'perfilencargadoadquisiciones');
INSERT INTO public.django_content_type VALUES (9, 'usuarios', 'perfiljefeproyecto');
INSERT INTO public.django_content_type VALUES (10, 'proveedores', 'proveedor');
INSERT INTO public.django_content_type VALUES (11, 'proyectos', 'proyecto');
INSERT INTO public.django_content_type VALUES (12, 'proyectos', 'itemizado');
INSERT INTO public.django_content_type VALUES (13, 'inventario', 'material');
INSERT INTO public.django_content_type VALUES (14, 'solicitudes', 'solicitudmaterial');
INSERT INTO public.django_content_type VALUES (15, 'solicitudes', 'solicituddetalle');
INSERT INTO public.django_content_type VALUES (16, 'proveedores', 'proveedormaterial');
INSERT INTO public.django_content_type VALUES (17, 'inventario', 'movimientoinventario');
INSERT INTO public.django_content_type VALUES (18, 'inventario', 'prestamoherramienta');
INSERT INTO public.django_content_type VALUES (19, 'solicitudes', 'solicitudadjunto');
INSERT INTO public.django_content_type VALUES (20, 'adquisiciones', 'cotizacion');
INSERT INTO public.django_content_type VALUES (21, 'adquisiciones', 'ordencompra');
INSERT INTO public.django_content_type VALUES (22, 'adquisiciones', 'ordencompralinea');
INSERT INTO public.django_content_type VALUES (23, 'adquisiciones', 'cotizacionlinea');
INSERT INTO public.django_content_type VALUES (24, 'facturacion', 'factura');
INSERT INTO public.django_content_type VALUES (25, 'proyectos', 'tipodocumento');
INSERT INTO public.django_content_type VALUES (26, 'proyectos', 'archivoproyecto');
INSERT INTO public.django_content_type VALUES (27, 'auditoria', 'registroauditoria');
INSERT INTO public.django_content_type VALUES (28, 'usuarios', 'parametrossistema');
INSERT INTO public.django_content_type VALUES (29, 'usuarios', 'solicitudcambioperfil');
INSERT INTO public.django_content_type VALUES (30, 'usuarios', 'intentoacceso');
INSERT INTO public.django_content_type VALUES (31, 'usuarios', 'notificacion');


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.auth_permission VALUES (1, 'Can add log entry', 1, 'add_logentry');
INSERT INTO public.auth_permission VALUES (2, 'Can change log entry', 1, 'change_logentry');
INSERT INTO public.auth_permission VALUES (3, 'Can delete log entry', 1, 'delete_logentry');
INSERT INTO public.auth_permission VALUES (4, 'Can view log entry', 1, 'view_logentry');
INSERT INTO public.auth_permission VALUES (5, 'Can add permission', 2, 'add_permission');
INSERT INTO public.auth_permission VALUES (6, 'Can change permission', 2, 'change_permission');
INSERT INTO public.auth_permission VALUES (7, 'Can delete permission', 2, 'delete_permission');
INSERT INTO public.auth_permission VALUES (8, 'Can view permission', 2, 'view_permission');
INSERT INTO public.auth_permission VALUES (9, 'Can add group', 3, 'add_group');
INSERT INTO public.auth_permission VALUES (10, 'Can change group', 3, 'change_group');
INSERT INTO public.auth_permission VALUES (11, 'Can delete group', 3, 'delete_group');
INSERT INTO public.auth_permission VALUES (12, 'Can view group', 3, 'view_group');
INSERT INTO public.auth_permission VALUES (13, 'Can add content type', 4, 'add_contenttype');
INSERT INTO public.auth_permission VALUES (14, 'Can change content type', 4, 'change_contenttype');
INSERT INTO public.auth_permission VALUES (15, 'Can delete content type', 4, 'delete_contenttype');
INSERT INTO public.auth_permission VALUES (16, 'Can view content type', 4, 'view_contenttype');
INSERT INTO public.auth_permission VALUES (17, 'Can add session', 5, 'add_session');
INSERT INTO public.auth_permission VALUES (18, 'Can change session', 5, 'change_session');
INSERT INTO public.auth_permission VALUES (19, 'Can delete session', 5, 'delete_session');
INSERT INTO public.auth_permission VALUES (20, 'Can view session', 5, 'view_session');
INSERT INTO public.auth_permission VALUES (21, 'Can add Usuario', 6, 'add_usuario');
INSERT INTO public.auth_permission VALUES (22, 'Can change Usuario', 6, 'change_usuario');
INSERT INTO public.auth_permission VALUES (23, 'Can delete Usuario', 6, 'delete_usuario');
INSERT INTO public.auth_permission VALUES (24, 'Can view Usuario', 6, 'view_usuario');
INSERT INTO public.auth_permission VALUES (25, 'Can add Perfil Bodeguero', 7, 'add_perfilbodeguero');
INSERT INTO public.auth_permission VALUES (26, 'Can change Perfil Bodeguero', 7, 'change_perfilbodeguero');
INSERT INTO public.auth_permission VALUES (27, 'Can delete Perfil Bodeguero', 7, 'delete_perfilbodeguero');
INSERT INTO public.auth_permission VALUES (28, 'Can view Perfil Bodeguero', 7, 'view_perfilbodeguero');
INSERT INTO public.auth_permission VALUES (29, 'Can add Perfil Encargado de Adquisiciones', 8, 'add_perfilencargadoadquisiciones');
INSERT INTO public.auth_permission VALUES (30, 'Can change Perfil Encargado de Adquisiciones', 8, 'change_perfilencargadoadquisiciones');
INSERT INTO public.auth_permission VALUES (31, 'Can delete Perfil Encargado de Adquisiciones', 8, 'delete_perfilencargadoadquisiciones');
INSERT INTO public.auth_permission VALUES (32, 'Can view Perfil Encargado de Adquisiciones', 8, 'view_perfilencargadoadquisiciones');
INSERT INTO public.auth_permission VALUES (33, 'Can add Perfil Jefe de Proyecto', 9, 'add_perfiljefeproyecto');
INSERT INTO public.auth_permission VALUES (34, 'Can change Perfil Jefe de Proyecto', 9, 'change_perfiljefeproyecto');
INSERT INTO public.auth_permission VALUES (35, 'Can delete Perfil Jefe de Proyecto', 9, 'delete_perfiljefeproyecto');
INSERT INTO public.auth_permission VALUES (36, 'Can view Perfil Jefe de Proyecto', 9, 'view_perfiljefeproyecto');
INSERT INTO public.auth_permission VALUES (37, 'Can add Proveedor', 10, 'add_proveedor');
INSERT INTO public.auth_permission VALUES (38, 'Can change Proveedor', 10, 'change_proveedor');
INSERT INTO public.auth_permission VALUES (39, 'Can delete Proveedor', 10, 'delete_proveedor');
INSERT INTO public.auth_permission VALUES (40, 'Can view Proveedor', 10, 'view_proveedor');
INSERT INTO public.auth_permission VALUES (41, 'Can add Proyecto', 11, 'add_proyecto');
INSERT INTO public.auth_permission VALUES (42, 'Can change Proyecto', 11, 'change_proyecto');
INSERT INTO public.auth_permission VALUES (43, 'Can delete Proyecto', 11, 'delete_proyecto');
INSERT INTO public.auth_permission VALUES (44, 'Can view Proyecto', 11, 'view_proyecto');
INSERT INTO public.auth_permission VALUES (45, 'Can add Itemizado', 12, 'add_itemizado');
INSERT INTO public.auth_permission VALUES (46, 'Can change Itemizado', 12, 'change_itemizado');
INSERT INTO public.auth_permission VALUES (47, 'Can delete Itemizado', 12, 'delete_itemizado');
INSERT INTO public.auth_permission VALUES (48, 'Can view Itemizado', 12, 'view_itemizado');
INSERT INTO public.auth_permission VALUES (49, 'Can add Material', 13, 'add_material');
INSERT INTO public.auth_permission VALUES (50, 'Can change Material', 13, 'change_material');
INSERT INTO public.auth_permission VALUES (51, 'Can delete Material', 13, 'delete_material');
INSERT INTO public.auth_permission VALUES (52, 'Can view Material', 13, 'view_material');
INSERT INTO public.auth_permission VALUES (53, 'Can add Solicitud de material', 14, 'add_solicitudmaterial');
INSERT INTO public.auth_permission VALUES (54, 'Can change Solicitud de material', 14, 'change_solicitudmaterial');
INSERT INTO public.auth_permission VALUES (55, 'Can delete Solicitud de material', 14, 'delete_solicitudmaterial');
INSERT INTO public.auth_permission VALUES (56, 'Can view Solicitud de material', 14, 'view_solicitudmaterial');
INSERT INTO public.auth_permission VALUES (57, 'Can add Detalle de solicitud', 15, 'add_solicituddetalle');
INSERT INTO public.auth_permission VALUES (58, 'Can change Detalle de solicitud', 15, 'change_solicituddetalle');
INSERT INTO public.auth_permission VALUES (59, 'Can delete Detalle de solicitud', 15, 'delete_solicituddetalle');
INSERT INTO public.auth_permission VALUES (60, 'Can view Detalle de solicitud', 15, 'view_solicituddetalle');
INSERT INTO public.auth_permission VALUES (61, 'Can add Material del proveedor', 16, 'add_proveedormaterial');
INSERT INTO public.auth_permission VALUES (62, 'Can change Material del proveedor', 16, 'change_proveedormaterial');
INSERT INTO public.auth_permission VALUES (63, 'Can delete Material del proveedor', 16, 'delete_proveedormaterial');
INSERT INTO public.auth_permission VALUES (64, 'Can view Material del proveedor', 16, 'view_proveedormaterial');
INSERT INTO public.auth_permission VALUES (65, 'Can add Movimiento de inventario', 17, 'add_movimientoinventario');
INSERT INTO public.auth_permission VALUES (66, 'Can change Movimiento de inventario', 17, 'change_movimientoinventario');
INSERT INTO public.auth_permission VALUES (67, 'Can delete Movimiento de inventario', 17, 'delete_movimientoinventario');
INSERT INTO public.auth_permission VALUES (68, 'Can view Movimiento de inventario', 17, 'view_movimientoinventario');
INSERT INTO public.auth_permission VALUES (69, 'Can add Préstamo de herramienta', 18, 'add_prestamoherramienta');
INSERT INTO public.auth_permission VALUES (70, 'Can change Préstamo de herramienta', 18, 'change_prestamoherramienta');
INSERT INTO public.auth_permission VALUES (71, 'Can delete Préstamo de herramienta', 18, 'delete_prestamoherramienta');
INSERT INTO public.auth_permission VALUES (72, 'Can view Préstamo de herramienta', 18, 'view_prestamoherramienta');
INSERT INTO public.auth_permission VALUES (73, 'Can add Adjunto de solicitud', 19, 'add_solicitudadjunto');
INSERT INTO public.auth_permission VALUES (74, 'Can change Adjunto de solicitud', 19, 'change_solicitudadjunto');
INSERT INTO public.auth_permission VALUES (75, 'Can delete Adjunto de solicitud', 19, 'delete_solicitudadjunto');
INSERT INTO public.auth_permission VALUES (76, 'Can view Adjunto de solicitud', 19, 'view_solicitudadjunto');
INSERT INTO public.auth_permission VALUES (77, 'Can add Cotización', 20, 'add_cotizacion');
INSERT INTO public.auth_permission VALUES (78, 'Can change Cotización', 20, 'change_cotizacion');
INSERT INTO public.auth_permission VALUES (79, 'Can delete Cotización', 20, 'delete_cotizacion');
INSERT INTO public.auth_permission VALUES (80, 'Can view Cotización', 20, 'view_cotizacion');
INSERT INTO public.auth_permission VALUES (81, 'Can add Orden de compra', 21, 'add_ordencompra');
INSERT INTO public.auth_permission VALUES (82, 'Can change Orden de compra', 21, 'change_ordencompra');
INSERT INTO public.auth_permission VALUES (83, 'Can delete Orden de compra', 21, 'delete_ordencompra');
INSERT INTO public.auth_permission VALUES (84, 'Can view Orden de compra', 21, 'view_ordencompra');
INSERT INTO public.auth_permission VALUES (85, 'Can add Línea de orden de compra', 22, 'add_ordencompralinea');
INSERT INTO public.auth_permission VALUES (86, 'Can change Línea de orden de compra', 22, 'change_ordencompralinea');
INSERT INTO public.auth_permission VALUES (87, 'Can delete Línea de orden de compra', 22, 'delete_ordencompralinea');
INSERT INTO public.auth_permission VALUES (88, 'Can view Línea de orden de compra', 22, 'view_ordencompralinea');
INSERT INTO public.auth_permission VALUES (89, 'Can add Línea de cotización', 23, 'add_cotizacionlinea');
INSERT INTO public.auth_permission VALUES (90, 'Can change Línea de cotización', 23, 'change_cotizacionlinea');
INSERT INTO public.auth_permission VALUES (91, 'Can delete Línea de cotización', 23, 'delete_cotizacionlinea');
INSERT INTO public.auth_permission VALUES (92, 'Can view Línea de cotización', 23, 'view_cotizacionlinea');
INSERT INTO public.auth_permission VALUES (93, 'Can add Factura', 24, 'add_factura');
INSERT INTO public.auth_permission VALUES (94, 'Can change Factura', 24, 'change_factura');
INSERT INTO public.auth_permission VALUES (95, 'Can delete Factura', 24, 'delete_factura');
INSERT INTO public.auth_permission VALUES (96, 'Can view Factura', 24, 'view_factura');
INSERT INTO public.auth_permission VALUES (97, 'Can add Tipo de documento', 25, 'add_tipodocumento');
INSERT INTO public.auth_permission VALUES (98, 'Can change Tipo de documento', 25, 'change_tipodocumento');
INSERT INTO public.auth_permission VALUES (99, 'Can delete Tipo de documento', 25, 'delete_tipodocumento');
INSERT INTO public.auth_permission VALUES (100, 'Can view Tipo de documento', 25, 'view_tipodocumento');
INSERT INTO public.auth_permission VALUES (101, 'Can add Archivo del proyecto', 26, 'add_archivoproyecto');
INSERT INTO public.auth_permission VALUES (102, 'Can change Archivo del proyecto', 26, 'change_archivoproyecto');
INSERT INTO public.auth_permission VALUES (103, 'Can delete Archivo del proyecto', 26, 'delete_archivoproyecto');
INSERT INTO public.auth_permission VALUES (104, 'Can view Archivo del proyecto', 26, 'view_archivoproyecto');
INSERT INTO public.auth_permission VALUES (105, 'Can add Registro de auditoría', 27, 'add_registroauditoria');
INSERT INTO public.auth_permission VALUES (106, 'Can change Registro de auditoría', 27, 'change_registroauditoria');
INSERT INTO public.auth_permission VALUES (107, 'Can delete Registro de auditoría', 27, 'delete_registroauditoria');
INSERT INTO public.auth_permission VALUES (108, 'Can view Registro de auditoría', 27, 'view_registroauditoria');
INSERT INTO public.auth_permission VALUES (109, 'Can add Parámetros del sistema', 28, 'add_parametrossistema');
INSERT INTO public.auth_permission VALUES (110, 'Can change Parámetros del sistema', 28, 'change_parametrossistema');
INSERT INTO public.auth_permission VALUES (111, 'Can delete Parámetros del sistema', 28, 'delete_parametrossistema');
INSERT INTO public.auth_permission VALUES (112, 'Can view Parámetros del sistema', 28, 'view_parametrossistema');
INSERT INTO public.auth_permission VALUES (113, 'Can add Solicitud de cambio de datos', 29, 'add_solicitudcambioperfil');
INSERT INTO public.auth_permission VALUES (114, 'Can change Solicitud de cambio de datos', 29, 'change_solicitudcambioperfil');
INSERT INTO public.auth_permission VALUES (115, 'Can delete Solicitud de cambio de datos', 29, 'delete_solicitudcambioperfil');
INSERT INTO public.auth_permission VALUES (116, 'Can view Solicitud de cambio de datos', 29, 'view_solicitudcambioperfil');
INSERT INTO public.auth_permission VALUES (117, 'Can add Intento de acceso', 30, 'add_intentoacceso');
INSERT INTO public.auth_permission VALUES (118, 'Can change Intento de acceso', 30, 'change_intentoacceso');
INSERT INTO public.auth_permission VALUES (119, 'Can delete Intento de acceso', 30, 'delete_intentoacceso');
INSERT INTO public.auth_permission VALUES (120, 'Can view Intento de acceso', 30, 'view_intentoacceso');
INSERT INTO public.auth_permission VALUES (121, 'Can add Notificación', 31, 'add_notificacion');
INSERT INTO public.auth_permission VALUES (122, 'Can change Notificación', 31, 'change_notificacion');
INSERT INTO public.auth_permission VALUES (123, 'Can delete Notificación', 31, 'delete_notificacion');
INSERT INTO public.auth_permission VALUES (124, 'Can view Notificación', 31, 'view_notificacion');


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_migrations VALUES (1, 'contenttypes', '0001_initial', '2026-06-05 23:31:23.313055-04');
INSERT INTO public.django_migrations VALUES (2, 'contenttypes', '0002_remove_content_type_name', '2026-06-05 23:31:23.322064-04');
INSERT INTO public.django_migrations VALUES (3, 'auth', '0001_initial', '2026-06-05 23:31:23.350656-04');
INSERT INTO public.django_migrations VALUES (4, 'auth', '0002_alter_permission_name_max_length', '2026-06-05 23:31:23.353657-04');
INSERT INTO public.django_migrations VALUES (5, 'auth', '0003_alter_user_email_max_length', '2026-06-05 23:31:23.355658-04');
INSERT INTO public.django_migrations VALUES (6, 'auth', '0004_alter_user_username_opts', '2026-06-05 23:31:23.357658-04');
INSERT INTO public.django_migrations VALUES (7, 'auth', '0005_alter_user_last_login_null', '2026-06-05 23:31:23.360659-04');
INSERT INTO public.django_migrations VALUES (8, 'auth', '0006_require_contenttypes_0002', '2026-06-05 23:31:23.361663-04');
INSERT INTO public.django_migrations VALUES (9, 'auth', '0007_alter_validators_add_error_messages', '2026-06-05 23:31:23.363203-04');
INSERT INTO public.django_migrations VALUES (10, 'auth', '0008_alter_user_username_max_length', '2026-06-05 23:31:23.365665-04');
INSERT INTO public.django_migrations VALUES (11, 'auth', '0009_alter_user_last_name_max_length', '2026-06-05 23:31:23.367623-04');
INSERT INTO public.django_migrations VALUES (12, 'auth', '0010_alter_group_name_max_length', '2026-06-05 23:31:23.372622-04');
INSERT INTO public.django_migrations VALUES (13, 'auth', '0011_update_proxy_permissions', '2026-06-05 23:31:23.374622-04');
INSERT INTO public.django_migrations VALUES (14, 'auth', '0012_alter_user_first_name_max_length', '2026-06-05 23:31:23.375623-04');
INSERT INTO public.django_migrations VALUES (15, 'usuarios', '0001_initial', '2026-06-05 23:31:23.426561-04');
INSERT INTO public.django_migrations VALUES (16, 'admin', '0001_initial', '2026-06-05 23:31:23.436561-04');
INSERT INTO public.django_migrations VALUES (17, 'admin', '0002_logentry_remove_auto_add', '2026-06-05 23:31:23.440562-04');
INSERT INTO public.django_migrations VALUES (18, 'admin', '0003_logentry_add_action_flag_choices', '2026-06-05 23:31:23.444563-04');
INSERT INTO public.django_migrations VALUES (19, 'inventario', '0001_initial', '2026-06-05 23:31:23.449562-04');
INSERT INTO public.django_migrations VALUES (20, 'proveedores', '0001_initial', '2026-06-05 23:31:23.454563-04');
INSERT INTO public.django_migrations VALUES (21, 'proyectos', '0001_initial', '2026-06-05 23:31:23.463504-04');
INSERT INTO public.django_migrations VALUES (22, 'sessions', '0001_initial', '2026-06-05 23:31:23.469026-04');
INSERT INTO public.django_migrations VALUES (23, 'solicitudes', '0001_initial', '2026-06-05 23:31:23.478026-04');
INSERT INTO public.django_migrations VALUES (24, 'solicitudes', '0002_initial', '2026-06-05 23:31:23.495026-04');
INSERT INTO public.django_migrations VALUES (25, 'proyectos', '0002_initial', '2026-06-10 21:47:24.933564-04');
INSERT INTO public.django_migrations VALUES (26, 'usuarios', '0002_usuario_pendiente_aprobacion', '2026-06-10 22:46:10.210209-04');
INSERT INTO public.django_migrations VALUES (27, 'solicitudes', '0003_incremento2_justificacion_adjuntos', '2026-09-07 20:09:11.795055-03');
INSERT INTO public.django_migrations VALUES (28, 'adquisiciones', '0001_initial', '2026-09-07 20:09:11.863499-03');
INSERT INTO public.django_migrations VALUES (29, 'facturacion', '0001_initial', '2026-09-07 20:09:11.893291-03');
INSERT INTO public.django_migrations VALUES (30, 'inventario', '0002_bodega_incremento2', '2026-09-07 20:09:11.930626-03');
INSERT INTO public.django_migrations VALUES (31, 'proveedores', '0002_proveedormaterial', '2026-09-07 20:09:11.948408-03');
INSERT INTO public.django_migrations VALUES (32, 'proyectos', '0003_proyecto_centro_costo', '2026-09-07 20:09:11.953917-03');
INSERT INTO public.django_migrations VALUES (33, 'usuarios', '0003_usuario_rol_contabilidad', '2026-09-07 20:09:11.959917-03');
INSERT INTO public.django_migrations VALUES (34, 'inventario', '0003_alter_movimientoinventario_jefe_proyecto_and_more', '2026-09-11 19:41:56.279639-03');
INSERT INTO public.django_migrations VALUES (35, 'proveedores', '0003_proveedormaterial_condicion_pago_and_more', '2026-09-11 19:41:56.327766-03');
INSERT INTO public.django_migrations VALUES (36, 'proyectos', '0004_alter_proyecto_jefe_proyecto', '2026-09-11 19:41:56.336463-03');
INSERT INTO public.django_migrations VALUES (37, 'proveedores', '0004_proveedormaterial_material', '2026-09-11 20:20:02.85666-03');
INSERT INTO public.django_migrations VALUES (38, 'solicitudes', '0004_solicituddetalle_detalle_solicituddetalle_proveedor_and_more', '2026-09-11 20:20:02.905316-03');
INSERT INTO public.django_migrations VALUES (39, 'auditoria', '0001_initial', '2026-09-13 01:40:25.030097-03');
INSERT INTO public.django_migrations VALUES (40, 'proyectos', '0005_tipodocumento_archivoproyecto', '2026-09-13 01:40:25.060994-03');
INSERT INTO public.django_migrations VALUES (41, 'auditoria', '0002_alter_registroauditoria_accion_and_more', '2026-09-28 22:59:30.518935-03');
INSERT INTO public.django_migrations VALUES (42, 'inventario', '0004_material_categoria_material_codigo_interno', '2026-09-28 22:59:30.591127-03');
INSERT INTO public.django_migrations VALUES (43, 'inventario', '0005_codigos_internos_existentes', '2026-09-28 22:59:30.6096-03');
INSERT INTO public.django_migrations VALUES (44, 'inventario', '0006_codigo_interno_unico', '2026-09-28 22:59:30.618337-03');
INSERT INTO public.django_migrations VALUES (45, 'proyectos', '0006_archivoproyecto_bloqueado_desde_and_more', '2026-09-28 22:59:30.678006-03');
INSERT INTO public.django_migrations VALUES (46, 'solicitudes', '0005_solicitudmaterial_motivo_rechazo', '2026-09-28 22:59:30.688295-03');
INSERT INTO public.django_migrations VALUES (47, 'usuarios', '0004_parametrossistema', '2026-09-28 22:59:30.719218-03');
INSERT INTO public.django_migrations VALUES (48, 'auditoria', '0003_alter_registroauditoria_accion', '2026-10-02 13:34:20.668797-03');
INSERT INTO public.django_migrations VALUES (49, 'proveedores', '0005_remove_proveedormaterial_condicion_pago', '2026-10-02 13:34:20.735092-03');
INSERT INTO public.django_migrations VALUES (50, 'usuarios', '0005_usuario_foto_solicitudcambioperfil', '2026-10-02 13:34:20.828108-03');
INSERT INTO public.django_migrations VALUES (51, 'adquisiciones', '0002_ordencompra_proyecto_alter_ordencompra_solicitud', '2026-11-03 12:08:47.750285-03');
INSERT INTO public.django_migrations VALUES (52, 'proyectos', '0007_proyecto_jefes', '2026-11-03 12:08:47.809736-03');
INSERT INTO public.django_migrations VALUES (53, 'adquisiciones', '0003_ordencompra_folio_ordencompra_folio_con_punto', '2026-11-03 14:33:02.935248-03');
INSERT INTO public.django_migrations VALUES (54, 'proveedores', '0006_proveedor_comuna_proveedor_direccion_proveedor_giro', '2026-11-03 14:33:02.955501-03');
INSERT INTO public.django_migrations VALUES (55, 'usuarios', '0006_parametrossistema_siguiente_folio_oc', '2026-11-03 14:33:02.967656-03');
INSERT INTO public.django_migrations VALUES (56, 'adquisiciones', '0004_proveedor_direccion_snapshot', '2026-11-14 17:28:05.667569-03');
INSERT INTO public.django_migrations VALUES (57, 'auditoria', '0004_operacion_crud', '2026-11-14 17:28:05.703628-03');
INSERT INTO public.django_migrations VALUES (58, 'auditoria', '0005_accion_itemizado', '2026-11-14 17:28:05.72418-03');
INSERT INTO public.django_migrations VALUES (59, 'facturacion', '0002_monto_con_iva', '2026-11-14 17:28:05.732834-03');
INSERT INTO public.django_migrations VALUES (60, 'solicitudes', '0006_estados_rf15_y_correlativo_al_emitir', '2026-11-14 17:28:05.762291-03');
INSERT INTO public.django_migrations VALUES (61, 'proyectos', '0008_quita_estado_suspendido', '2026-11-14 17:28:05.780616-03');
INSERT INTO public.django_migrations VALUES (62, 'proyectos', '0009_tipos_documento_rf51', '2026-11-14 17:28:05.79627-03');
INSERT INTO public.django_migrations VALUES (63, 'inventario', '0007_salida_partida', '2026-11-14 17:28:05.812349-03');
INSERT INTO public.django_migrations VALUES (64, 'inventario', '0008_partida_de_salidas_antiguas', '2026-11-14 17:28:05.838161-03');
INSERT INTO public.django_migrations VALUES (65, 'proveedores', '0007_proveedor_modificado', '2026-11-14 17:28:05.87193-03');
INSERT INTO public.django_migrations VALUES (66, 'usuarios', '0007_intentoacceso', '2026-11-14 17:28:05.883214-03');
INSERT INTO public.django_migrations VALUES (67, 'usuarios', '0008_notificacion', '2026-11-14 17:28:05.900965-03');


--
-- Data for Name: facturacion_factura; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.facturacion_factura VALUES (1, 'F-9001', '2026-09-07', '2026-10-07', 577000, '', 'REGISTRADA', 0.00, '', '2026-09-07 20:09:12.750599-03', NULL, NULL, 1, 20);
INSERT INTO public.facturacion_factura VALUES (2, '33415', '2026-07-16', '2026-09-14', 2330000, '', 'REGISTRADA', 0.00, '', '2026-10-04 00:30:55.892761-03', NULL, NULL, 4, 20);
INSERT INTO public.facturacion_factura VALUES (3, '118902', '2026-07-18', '2026-08-17', 2137104, '', 'REGISTRADA', 8.00, 'Diferencia corresponde a flete adicional acordado por correo con el JP.', '2026-10-04 00:30:55.898911-03', '2026-10-04 00:30:55.899934-03', 1, 11, 20);
INSERT INTO public.facturacion_factura VALUES (4, '7781', '2026-09-09', '2026-10-09', 1152500, '', 'REGISTRADA', 0.00, '', '2026-10-04 00:30:55.901473-03', NULL, NULL, 12, 20);
INSERT INTO public.facturacion_factura VALUES (5, 'A-5520', '2026-10-01', '2026-11-30', 2093952, '', 'BLOQUEADA', 12.00, '', '2026-10-04 00:30:55.903522-03', NULL, NULL, 2, 20);


--
-- Data for Name: facturacion_factura_ordenes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.facturacion_factura_ordenes VALUES (1, 1, 1);
INSERT INTO public.facturacion_factura_ordenes VALUES (2, 2, 9);
INSERT INTO public.facturacion_factura_ordenes VALUES (3, 3, 10);
INSERT INTO public.facturacion_factura_ordenes VALUES (4, 4, 6);
INSERT INTO public.facturacion_factura_ordenes VALUES (5, 5, 7);


--
-- Data for Name: inventario_movimientoinventario; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.inventario_movimientoinventario VALUES (1, 'ENTRADA', 80.00, 'Bodega central · Estante A1', '', '', '', '2026-09-07 20:09:12.739084-03', NULL, 1, 1, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (3, 'MERMA', 120.00, '', '', 'DANO', 'Pallet caído en descarga.', '2026-09-07 20:09:12.745843-03', NULL, 10, NULL, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (4, 'ENTRADA', 250.00, 'Bodega central · Estante A1', 'GD-55120', '', '', '2026-10-04 00:30:55.828584-03', NULL, 1, 6, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (5, 'ENTRADA', 20.00, 'Bodega central', 'GD-77801', '', '', '2026-10-04 00:30:55.834735-03', NULL, 29, 7, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (6, 'ENTRADA', 75.00, 'Bodega central', 'GD-77801', '', '', '2026-10-04 00:30:55.837817-03', NULL, 7, 7, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (7, 'ENTRADA', 300.00, 'Bodega central', 'GD-30011', '', '', '2026-10-04 00:30:55.861446-03', NULL, 11, 9, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (8, 'ENTRADA', 120.00, 'Bodega central · Estante C4', 'GD-30012', '', '', '2026-10-04 00:30:55.865559-03', NULL, 12, 10, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (9, 'ENTRADA', 60.00, 'Bodega central · Estante A1', 'GD-90001', '', '', '2026-10-04 00:30:55.87582-03', NULL, 1, 11, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (15, 'SALIDA', 60.00, '', 'GD-2006', '', '', '2026-10-04 00:30:55.881981-03', 2, 15, NULL, 2, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (16, 'ENTRADA', 10.00, 'Bodega central · Estante B2', '', '', 'Sobrante al cierre de obra.', '2026-10-04 00:30:55.882495-03', NULL, 11, NULL, 4, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (17, 'MERMA', 25.00, '', '', 'ROBO', 'Faltante detectado en inventario semanal.', '2026-10-04 00:30:55.883522-03', NULL, 14, NULL, NULL, 12, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (18, 'MERMA', 8.00, '', '', 'DANO', 'Sacos humedecidos por lluvia.', '2026-10-04 00:30:55.884037-03', NULL, 1, NULL, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (19, 'DEVOLUCION_PROVEEDOR', 2.00, '', 'GD-DEV-01', 'DEFECTUOSO', 'Mallas con soldaduras cortadas.', '2026-10-04 00:30:55.884549-03', NULL, 29, 7, NULL, 4, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (20, 'ENTRADA', 1.00, 'Contenedor obra A', '', '', '', '2026-10-04 02:03:43.343226-03', NULL, 12, 4, NULL, 1, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (21, 'SALIDA', 1.00, '', '2033', '', '', '2026-10-04 02:04:20.955602-03', 7, 1, NULL, 5, 1, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (22, 'MERMA', 1.00, '', '', 'DANO', '', '2026-10-04 02:06:04.820681-03', NULL, 1, NULL, NULL, 1, NULL);
INSERT INTO public.inventario_movimientoinventario VALUES (13, 'SALIDA', 115.00, '', 'GD-2004', '', '', '2026-10-04 00:30:55.880438-03', 6, 12, NULL, 4, 4, 12);
INSERT INTO public.inventario_movimientoinventario VALUES (12, 'SALIDA', 290.00, '', 'GD-2003', '', '', '2026-10-04 00:30:55.879926-03', 6, 11, NULL, 4, 4, 11);
INSERT INTO public.inventario_movimientoinventario VALUES (11, 'SALIDA', 15.00, '', 'GD-2002', '', '', '2026-10-04 00:30:55.8789-03', 5, 29, NULL, 3, 12, 8);
INSERT INTO public.inventario_movimientoinventario VALUES (10, 'SALIDA', 150.00, '', 'GD-2001', '', '', '2026-10-04 00:30:55.878389-03', 5, 1, NULL, 3, 4, 8);
INSERT INTO public.inventario_movimientoinventario VALUES (2, 'SALIDA', 30.00, '', 'GD-1001', '', '', '2026-09-07 20:09:12.745093-03', 2, 1, NULL, 1, 4, 1);


--
-- Data for Name: inventario_prestamoherramienta; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.inventario_prestamoherramienta VALUES (1, '2026-09-07', '2026-09-22', NULL, 'PRESTADA', '2026-09-07 20:09:12.747601-03', 3, 2, 1, 4);
INSERT INTO public.inventario_prestamoherramienta VALUES (2, '2026-09-29', '2026-10-14', NULL, 'PRESTADA', '2026-10-04 00:30:55.886088-03', 17, 5, 3, 4);
INSERT INTO public.inventario_prestamoherramienta VALUES (3, '2026-09-04', '2026-09-27', NULL, 'PRESTADA', '2026-10-04 00:30:55.889163-03', 20, 2, 2, 4);
INSERT INTO public.inventario_prestamoherramienta VALUES (4, '2026-06-06', '2026-06-26', '2026-06-25', 'DEVUELTA', '2026-10-04 00:30:55.889679-03', 18, 6, 4, 4);
INSERT INTO public.inventario_prestamoherramienta VALUES (5, '2026-08-25', '2026-09-14', '2026-09-16', 'DEVUELTA', '2026-10-04 00:30:55.890708-03', 21, 5, 3, 4);
INSERT INTO public.inventario_prestamoherramienta VALUES (6, '2026-10-03', '2026-10-17', NULL, 'PRESTADA', '2026-10-04 02:05:32.910918-03', 21, 5, 3, 1);


--
-- Data for Name: proyectos_tipodocumento; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.proyectos_tipodocumento VALUES (1, 'Plano', 'Planimetría de arquitectura, estructura o especialidades', true);
INSERT INTO public.proyectos_tipodocumento VALUES (2, 'Contrato', 'Contrato de obra, subcontratos y anexos', true);
INSERT INTO public.proyectos_tipodocumento VALUES (3, 'Permiso municipal', 'Permisos de edificación y recepción municipal', true);
INSERT INTO public.proyectos_tipodocumento VALUES (4, 'Cotización', 'Cotizaciones recibidas de proveedores', true);
INSERT INTO public.proyectos_tipodocumento VALUES (5, 'Factura', 'Facturas y documentos tributarios del proyecto', true);
INSERT INTO public.proyectos_tipodocumento VALUES (6, 'Acta de recepción', 'Actas de recepción de obra y de materiales', true);
INSERT INTO public.proyectos_tipodocumento VALUES (7, 'Informe técnico', 'Informes de ensayo, topografía y mecánica de suelos', true);
INSERT INTO public.proyectos_tipodocumento VALUES (8, 'Especificación Técnica', 'Especificaciones técnicas de la obra', true);
INSERT INTO public.proyectos_tipodocumento VALUES (9, 'Plano 2D', 'Planimetría en 2D (DWG, DXF, PDF)', true);
INSERT INTO public.proyectos_tipodocumento VALUES (10, 'Plano 3D', 'Modelos 3D (IFC, RVT, SKP)', true);
INSERT INTO public.proyectos_tipodocumento VALUES (11, 'Fotografía', 'Registro fotográfico de la obra', true);
INSERT INTO public.proyectos_tipodocumento VALUES (12, 'Videos', 'Registro en video de la obra', true);


--
-- Data for Name: proyectos_archivoproyecto; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: proyectos_proyecto_jefes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.proyectos_proyecto_jefes VALUES (1, 5, 7);
INSERT INTO public.proyectos_proyecto_jefes VALUES (2, 3, 5);
INSERT INTO public.proyectos_proyecto_jefes VALUES (3, 1, 2);
INSERT INTO public.proyectos_proyecto_jefes VALUES (4, 2, 2);
INSERT INTO public.proyectos_proyecto_jefes VALUES (5, 4, 6);


--
-- Data for Name: solicitudes_solicitudadjunto; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: usuarios_notificacion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_notificacion VALUES (1, 'Solicitud SM-000011: En cotización', 'La solicitud SM-000011 de Centro Médico Ñuñoa cambió al estado «En cotización».

Todos los materiales tienen una cotización aprobada. Adquisiciones ya puede generar la orden de compra.', '/solicitudes/11/', false, '2026-11-14 17:40:24.163132-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (2, 'Solicitud SM-000025: Emitida', 'La solicitud SM-000025 de Centro Médico Ñuñoa cambió al estado «Emitida».

Emitida por Jefa de Proyecto, con 1 ítem(s).', '/solicitudes/26/', false, '2026-11-14 18:43:17.221342-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (3, 'Solicitud SM-000025 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000025 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/26/', false, '2026-11-14 18:43:18.481891-03', 3);
INSERT INTO public.usuarios_notificacion VALUES (4, 'Solicitud SM-000025 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000025 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/26/', false, '2026-11-14 18:43:18.481891-03', 8);
INSERT INTO public.usuarios_notificacion VALUES (5, 'Solicitud SM-000025 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000025 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/26/', false, '2026-11-14 18:43:18.481891-03', 9);
INSERT INTO public.usuarios_notificacion VALUES (6, 'Solicitud SM-000025 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000025 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/26/', false, '2026-11-14 18:43:18.481891-03', 10);
INSERT INTO public.usuarios_notificacion VALUES (7, 'Solicitud SM-000025 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000025 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/26/', false, '2026-11-14 18:43:18.481891-03', 23);
INSERT INTO public.usuarios_notificacion VALUES (8, 'Solicitud SM-000025: En cotización', 'La solicitud SM-000025 de Centro Médico Ñuñoa cambió al estado «En cotización».

Todos los materiales tienen una cotización aprobada. Adquisiciones ya puede generar la orden de compra.', '/solicitudes/26/', false, '2026-11-14 19:00:48.642981-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (9, 'Solicitud SM-000025: OC generada', 'La solicitud SM-000025 de Centro Médico Ñuñoa cambió al estado «OC generada».

Órdenes de compra generadas: 1 (Hormigones Bío-Bío S.A.). Quedan en borrador esperando la aprobación del Jefe de Proyecto.', '/solicitudes/26/', false, '2026-11-14 19:08:37.647661-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (10, 'Solicitud SM-000026: Emitida', 'La solicitud SM-000026 de Centro Médico Ñuñoa cambió al estado «Emitida».

Emitida por Jefa de Proyecto, con 1 ítem(s).', '/solicitudes/27/', false, '2026-11-14 19:14:55.147528-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (11, 'Solicitud SM-000026 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000026 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/27/', false, '2026-11-14 19:14:55.157081-03', 3);
INSERT INTO public.usuarios_notificacion VALUES (12, 'Solicitud SM-000026 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000026 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/27/', false, '2026-11-14 19:14:55.157081-03', 8);
INSERT INTO public.usuarios_notificacion VALUES (13, 'Solicitud SM-000026 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000026 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/27/', false, '2026-11-14 19:14:55.157081-03', 9);
INSERT INTO public.usuarios_notificacion VALUES (14, 'Solicitud SM-000026 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000026 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/27/', false, '2026-11-14 19:14:55.157081-03', 10);
INSERT INTO public.usuarios_notificacion VALUES (15, 'Solicitud SM-000026 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000026 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/27/', false, '2026-11-14 19:14:55.157081-03', 23);
INSERT INTO public.usuarios_notificacion VALUES (16, 'Solicitud SM-000026: En cotización', 'La solicitud SM-000026 de Centro Médico Ñuñoa cambió al estado «En cotización».

Todos los materiales tienen una cotización aprobada. Adquisiciones ya puede generar la orden de compra.', '/solicitudes/27/', false, '2026-11-14 19:15:49.083519-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (17, 'Solicitud SM-000027: Emitida', 'La solicitud SM-000027 de Centro Médico Ñuñoa cambió al estado «Emitida».

Emitida por Jefa de Proyecto, con 1 ítem(s).', '/solicitudes/28/', false, '2026-11-14 19:37:35.672445-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (18, 'Solicitud SM-000027 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000027 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/28/', false, '2026-11-14 19:37:35.677768-03', 3);
INSERT INTO public.usuarios_notificacion VALUES (19, 'Solicitud SM-000027 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000027 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/28/', false, '2026-11-14 19:37:35.677768-03', 8);
INSERT INTO public.usuarios_notificacion VALUES (20, 'Solicitud SM-000027 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000027 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/28/', false, '2026-11-14 19:37:35.677768-03', 9);
INSERT INTO public.usuarios_notificacion VALUES (21, 'Solicitud SM-000027 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000027 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/28/', false, '2026-11-14 19:37:35.677768-03', 10);
INSERT INTO public.usuarios_notificacion VALUES (22, 'Solicitud SM-000027 lista para cotizar', 'Jefa de Proyecto emitió la solicitud SM-000027 para Centro Médico Ñuñoa, con 1 ítem(s).', '/adquisiciones/cotizaciones/sm/28/', false, '2026-11-14 19:37:35.677768-03', 23);
INSERT INTO public.usuarios_notificacion VALUES (23, 'Solicitud SM-000027: En cotización', 'La solicitud SM-000027 de Centro Médico Ñuñoa cambió al estado «En cotización».

Todos los materiales tienen una cotización aprobada. Adquisiciones ya puede generar la orden de compra.', '/solicitudes/28/', false, '2026-11-14 19:38:56.266424-03', 2);
INSERT INTO public.usuarios_notificacion VALUES (24, 'Solicitud SM-000027: OC generada', 'La solicitud SM-000027 de Centro Médico Ñuñoa cambió al estado «OC generada».

Órdenes de compra generadas: 13285 (Hormigones Bío-Bío S.A.). Quedan en borrador esperando la aprobación del Jefe de Proyecto.', '/solicitudes/28/', false, '2026-11-14 19:40:00.633804-03', 2);


--
-- Data for Name: usuarios_parametrossistema; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_parametrossistema VALUES (1, 5.00, 10.00, 10, '2026-11-14 19:11:07.993527-03', 3, 13286);


--
-- Data for Name: usuarios_perfilbodeguero; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_perfilbodeguero VALUES (1, 'MANANA', 4);
INSERT INTO public.usuarios_perfilbodeguero VALUES (2, 'TARDE', 12);


--
-- Data for Name: usuarios_perfilencargadoadquisiciones; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_perfilencargadoadquisiciones VALUES (1, 2, 3);
INSERT INTO public.usuarios_perfilencargadoadquisiciones VALUES (2, 1, 8);


--
-- Data for Name: usuarios_perfiljefeproyecto; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_perfiljefeproyecto VALUES (1, 'Edificación', 2);
INSERT INTO public.usuarios_perfiljefeproyecto VALUES (2, 'Habitacional', 5);
INSERT INTO public.usuarios_perfiljefeproyecto VALUES (3, 'Remodelaciones', 6);
INSERT INTO public.usuarios_perfiljefeproyecto VALUES (4, 'Industrial', 7);


--
-- Data for Name: usuarios_solicitudcambioperfil; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuarios_solicitudcambioperfil VALUES (1, 'email', 'bodega@m5.cl', 'bodega.central@m5.cl', 'Cambio a la casilla compartida de bodega central.', 'PENDIENTE', '2026-10-04 00:30:55.707005-03', NULL, '', NULL, 4);


--
-- Data for Name: usuarios_usuario_groups; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: usuarios_usuario_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Name: adquisiciones_cotizacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.adquisiciones_cotizacion_id_seq', 21, true);


--
-- Name: adquisiciones_cotizacionlinea_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.adquisiciones_cotizacionlinea_id_seq', 29, true);


--
-- Name: adquisiciones_ordencompra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.adquisiciones_ordencompra_id_seq', 18, true);


--
-- Name: adquisiciones_ordencompralinea_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.adquisiciones_ordencompralinea_id_seq', 21, true);


--
-- Name: auditoria_registroauditoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auditoria_registroauditoria_id_seq', 109, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 124, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 31, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 67, true);


--
-- Name: facturacion_factura_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.facturacion_factura_id_seq', 5, true);


--
-- Name: facturacion_factura_ordenes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.facturacion_factura_ordenes_id_seq', 5, true);


--
-- Name: inventario_material_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventario_material_id_seq', 33, true);


--
-- Name: inventario_movimientoinventario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventario_movimientoinventario_id_seq', 22, true);


--
-- Name: inventario_prestamoherramienta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventario_prestamoherramienta_id_seq', 6, true);


--
-- Name: proveedores_proveedor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proveedores_proveedor_id_seq', 13, true);


--
-- Name: proveedores_proveedormaterial_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proveedores_proveedormaterial_id_seq', 24, true);


--
-- Name: proyectos_archivoproyecto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proyectos_archivoproyecto_id_seq', 1, false);


--
-- Name: proyectos_itemizado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proyectos_itemizado_id_seq', 13, true);


--
-- Name: proyectos_proyecto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proyectos_proyecto_id_seq', 5, true);


--
-- Name: proyectos_proyecto_jefes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proyectos_proyecto_jefes_id_seq', 5, true);


--
-- Name: proyectos_tipodocumento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proyectos_tipodocumento_id_seq', 12, true);


--
-- Name: solicitudes_solicitudadjunto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitudes_solicitudadjunto_id_seq', 1, false);


--
-- Name: solicitudes_solicituddetalle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitudes_solicituddetalle_id_seq', 43, true);


--
-- Name: solicitudes_solicitudmaterial_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitudes_solicitudmaterial_id_seq', 28, true);


--
-- Name: usuarios_intentoacceso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_intentoacceso_id_seq', 1, false);


--
-- Name: usuarios_notificacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_notificacion_id_seq', 24, true);


--
-- Name: usuarios_parametrossistema_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_parametrossistema_id_seq', 1, false);


--
-- Name: usuarios_perfilbodeguero_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_perfilbodeguero_id_seq', 2, true);


--
-- Name: usuarios_perfilencargadoadquisiciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_perfilencargadoadquisiciones_id_seq', 2, true);


--
-- Name: usuarios_perfiljefeproyecto_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_perfiljefeproyecto_id_seq', 4, true);


--
-- Name: usuarios_solicitudcambioperfil_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_solicitudcambioperfil_id_seq', 1, true);


--
-- Name: usuarios_usuario_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_usuario_groups_id_seq', 1, false);


--
-- Name: usuarios_usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_usuario_id_seq', 29, true);


--
-- Name: usuarios_usuario_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_usuario_user_permissions_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict UduJpW0zANYlRT0pE4BPr94uf8KBHuv9tvcLliIFvI7paSeNBdSUEGzZEnxOgPb

