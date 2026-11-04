# Códigos de las variables (anexo A de Realinho et al., 2022)

Fuente: Realinho, V., Machado, J., Baptista, L. y Martins, M. V. (2022). Predicting student
dropout and academic success. *Data, 7*(11), 146, anexo A (pp. 12-16). Artículo de acceso
abierto (CC BY 4.0). La traducción al español es propia y es la base de las etiquetas de
la ficha (tarea 6.2).

## Antes de usar estas tablas

El anexo numera las categorías de forma **correlativa** (carrera de 1 a 17), pero el
archivo de UCI trae los **códigos originales** del sistema portugués. **Verificado el
03/11** con `data/raw/fuente.json`: en nacionalidad (21 valores), modalidad de ingreso (18),
carrera (17) y título previo (17) aparecen todas las categorías y los códigos coinciden
exactamente con la columna «Código UCI» de estas tablas, en el mismo orden del anexo.
Estado civil usa 1 a 6, igual que el anexo.

Para el nivel educativo y la ocupación de los padres (tablas A6 y A7), el archivo usa
códigos propios (por ejemplo, ocupación 0 a 195); la descripción oficial está en
`data/raw/uci_metadata.json`, que baja `scripts/descargar_datos.py` desde Windows.

## Estado civil (Marital status), tabla A1

| Anexo | Original | Español |
|---|---|---|
| 1 | Single | Soltero/a |
| 2 | Married | Casado/a |
| 3 | Widower | Viudo/a |
| 4 | Divorced | Divorciado/a |
| 5 | Facto union | Unión de hecho |
| 6 | Legally separated | Separado/a legalmente |

## Nacionalidad (Nacionality), tabla A2

| Anexo | Código UCI | Original | Español |
|---|---|---|---|
| 1 | 1 | Portuguese | Portuguesa |
| 2 | 2 | German | Alemana |
| 3 | 6 | Spanish | Española |
| 4 | 11 | Italian | Italiana |
| 5 | 13 | Dutch | Neerlandesa |
| 6 | 14 | English | Inglesa |
| 7 | 17 | Lithuanian | Lituana |
| 8 | 21 | Angolan | Angoleña |
| 9 | 22 | Cape Verdean | Caboverdiana |
| 10 | 24 | Guinean | Guineana |
| 11 | 25 | Mozambican | Mozambiqueña |
| 12 | 26 | Santomean | Santotomense |
| 13 | 32 | Turkish | Turca |
| 14 | 41 | Brazilian | Brasileña |
| 15 | 62 | Romanian | Rumana |
| 16 | 100 | Moldova (Republic of) | Moldava |
| 17 | 101 | Mexican | Mexicana |
| 18 | 103 | Ukrainian | Ucraniana |
| 19 | 105 | Russian | Rusa |
| 20 | 108 | Cuban | Cubana |
| 21 | 109 | Colombian | Colombiana |

## Modalidad de ingreso (Application mode), tabla A3

| Anexo | Código UCI | Original | Español |
|---|---|---|---|
| 1 | 1 | 1st phase—general contingent | 1.ª fase, contingente general |
| 2 | 2 | Ordinance No. 612/93 | Ordenanza N.º 612/93 |
| 3 | 5 | 1st phase—special contingent (Azores Island) | 1.ª fase, contingente especial (Azores) |
| 4 | 7 | Holders of other higher courses | Con otro título superior |
| 5 | 10 | Ordinance No. 854-B/99 | Ordenanza N.º 854-B/99 |
| 6 | 15 | International student (bachelor) | Estudiante internacional |
| 7 | 16 | 1st phase—special contingent (Madeira Island) | 1.ª fase, contingente especial (Madeira) |
| 8 | 17 | 2nd phase—general contingent | 2.ª fase, contingente general |
| 9 | 18 | 3rd phase—general contingent | 3.ª fase, contingente general |
| 10 | 26 | Ordinance No. 533-A/99, item b2) (Different Plan) | Ordenanza N.º 533-A/99, b2 (otro plan) |
| 11 | 27 | Ordinance No. 533-A/99, item b3 (Other Institution) | Ordenanza N.º 533-A/99, b3 (otra institución) |
| 12 | 39 | Over 23 years old | Mayores de 23 años |
| 13 | 42 | Transfer | Pase |
| 14 | 43 | Change in course | Cambio de carrera |
| 15 | 44 | Technological specialization diploma holders | Con diploma de especialización tecnológica |
| 16 | 51 | Change in institution/course | Cambio de institución o carrera |
| 17 | 53 | Short cycle diploma holders | Con diploma de ciclo corto |
| 18 | 57 | Change in institution/course (International) | Cambio de institución o carrera (internacional) |

## Carrera (Course), tabla A4

| Anexo | Código UCI | Original | Español |
|---|---|---|---|
| 1 | 33 | Biofuel Production Technologies | Tecnologías de Producción de Biocombustibles |
| 2 | 171 | Animation and Multimedia Design | Diseño de Animación y Multimedia |
| 3 | 8014 | Social Service (evening attendance) | Servicio Social (nocturno) |
| 4 | 9003 | Agronomy | Agronomía |
| 5 | 9070 | Communication Design | Diseño de Comunicación |
| 6 | 9085 | Veterinary Nursing | Enfermería Veterinaria |
| 7 | 9119 | Informatics Engineering | Ingeniería Informática |
| 8 | 9130 | Equiniculture | Equinocultura |
| 9 | 9147 | Management | Gestión |
| 10 | 9238 | Social Service | Servicio Social |
| 11 | 9254 | Tourism | Turismo |
| 12 | 9500 | Nursing | Enfermería |
| 13 | 9556 | Oral Hygiene | Higiene Oral |
| 14 | 9670 | Advertising and Marketing Management | Gestión de Publicidad y Marketing |
| 15 | 9773 | Journalism and Communication | Periodismo y Comunicación |
| 16 | 9853 | Basic Education | Educación Básica |
| 17 | 9991 | Management (evening attendance) | Gestión (nocturno) |

## Título previo (Previous qualification), tabla A5

| Anexo | Código UCI | Original | Español |
|---|---|---|---|
| 1 | 1 | Secondary education | Secundario completo |
| 2 | 2 | Higher education—bachelor's degree | Superior: bachillerato |
| 3 | 3 | Higher education—degree | Superior: licenciatura |
| 4 | 4 | Higher education—master's degree | Superior: maestría |
| 5 | 5 | Higher education—doctorate | Superior: doctorado |
| 6 | 6 | Frequency of higher education | Estudios superiores sin terminar |
| 7 | 9 | 12th year of schooling—not completed | 12.º año incompleto |
| 8 | 10 | 11th year of schooling—not completed | 11.º año incompleto |
| 9 | 12 | Other—11th year of schooling | Otro: 11.º año |
| 10 | 14 | 10th year of schooling | 10.º año |
| 11 | 15 | 10th year of schooling—not completed | 10.º año incompleto |
| 12 | 19 | Basic education 3rd cycle (9th/10th/11th year) or equivalent | Básica, 3.er ciclo (9.º a 11.º año) |
| 13 | 38 | Basic education 2nd cycle (6th/7th/8th year) or equivalent | Básica, 2.º ciclo (6.º a 8.º año) |
| 14 | 39 | Technological specialization course | Curso de especialización tecnológica |
| 15 | 40 | Higher education—degree (1st cycle) | Superior: licenciatura (1.er ciclo) |
| 16 | 42 | Professional higher technical course | Curso técnico superior profesional |
| 17 | 43 | Higher education—master's degree (2nd cycle) | Superior: maestría (2.º ciclo) |

## Nivel educativo de la madre y del padre, tabla A6

34 categorías en el anexo (1 = «Secondary Education—12th Year of Schooling or
Equivalent» … 34 = «Higher Education—doctorate (3rd cycle)»; 24 = «Unknown»). Los
códigos de UCI difieren. Usar `data/raw/uci_metadata.json` como fuente y traducir en la
tarea 6.2. Para la ficha alcanza con agrupar en niveles comprensibles (sin estudios,
primario/básico, secundario, superior, desconocido), indicando la agrupación en el
informe.

## Ocupación de la madre y del padre, tabla A7

46 categorías en el anexo (1 = «Student», 2 = «Representatives of the Legislative Power
and Executive Bodies…», …, 12 = «Other Situation», 13 = «(blank)», …). Mismo criterio
que la tabla A6: fuente `uci_metadata.json` y agrupación por gran grupo para la ficha.

## Binarias, tablas A8 a A10

| Variable | 1 | 0 |
|---|---|---|
| Gender (genero) | masculino | femenino |
| Daytime/evening attendance (turno_diurno) | diurno | nocturno |
| Displaced, Scholarship holder, International | sí | no |
