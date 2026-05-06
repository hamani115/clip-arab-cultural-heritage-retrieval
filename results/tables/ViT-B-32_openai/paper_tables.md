# Tables for paper

## Dataset summary by source and category

| source            | category               |   num_images |
|:------------------|:-----------------------|-------------:|
| Wikimedia Commons | architecture_sites     |           12 |
| Wikimedia Commons | bahrain_museum_objects |           40 |
| Wikimedia Commons | manuscript_calligraphy |           40 |
| Wikimedia Commons | museum_interior        |           30 |
| Wikimedia Commons | pottery_ceramics       |           80 |
| Wikimedia Commons | sculptures_statues     |           40 |


## Source and license summary

| source            | country   | license       |   num_images |
|:------------------|:----------|:--------------|-------------:|
| Wikimedia Commons | Bahrain   | CC BY 2.0     |            2 |
| Wikimedia Commons | Bahrain   | CC BY 2.5     |            1 |
| Wikimedia Commons | Bahrain   | CC BY 3.0     |            1 |
| Wikimedia Commons | Bahrain   | CC BY 4.0     |            1 |
| Wikimedia Commons | Bahrain   | CC BY-SA 2.5  |            1 |
| Wikimedia Commons | Bahrain   | CC BY-SA 3.0  |           12 |
| Wikimedia Commons | Bahrain   | CC BY-SA 4.0  |           22 |
| Wikimedia Commons | Iraq      | CC BY-SA 4.0  |           78 |
| Wikimedia Commons | Iraq      | Public domain |            2 |
| Wikimedia Commons | Oman      | CC BY 2.0     |            4 |
| Wikimedia Commons | Oman      | CC BY-SA 4.0  |           37 |
| Wikimedia Commons | Oman      | Public domain |            1 |
| Wikimedia Commons | Qatar     | CC BY 2.0     |            1 |
| Wikimedia Commons | Qatar     | CC BY 4.0     |           45 |
| Wikimedia Commons | Qatar     | CC BY-SA 2.0  |            2 |
| Wikimedia Commons | Qatar     | CC BY-SA 3.0  |            3 |
| Wikimedia Commons | Qatar     | CC BY-SA 4.0  |           27 |
| Wikimedia Commons | Qatar     | Public domain |            2 |


## Retrieval metrics

| prompt_id   | prompt                                    | expected_category      | language   | prompt_style   |   total_relevant_in_dataset |   precision_at_1 |   precision_at_5 |   precision_at_10 |   recall_at_5 |   recall_at_10 |      mrr |
|:------------|:------------------------------------------|:-----------------------|:-----------|:---------------|----------------------------:|-----------------:|-----------------:|------------------:|--------------:|---------------:|---------:|
| p01         | an Arabic manuscript                      | manuscript_calligraphy | en         | generic        |                          40 |                1 |              1   |               0.9 |     0.125     |         0.225  | 1        |
| p02         | a museum artifact with Arabic calligraphy | manuscript_calligraphy | en         | contextual     |                          40 |                0 |              0.2 |               0.2 |     0.025     |         0.05   | 0.25     |
| p03         | an Islamic ceramic bowl                   | pottery_ceramics       | en         | generic        |                          80 |                1 |              1   |               0.9 |     0.0625    |         0.1125 | 1        |
| p04         | ancient pottery from a museum             | pottery_ceramics       | en         | contextual     |                          80 |                0 |              0.6 |               0.8 |     0.0375    |         0.1    | 0.5      |
| p05         | a statue from an Arab museum              | sculptures_statues     | en         | generic        |                          40 |                1 |              1   |               1   |     0.125     |         0.25   | 1        |
| p06         | a sculpture displayed in a museum         | sculptures_statues     | en         | contextual     |                          40 |                0 |              0.6 |               0.7 |     0.075     |         0.175  | 0.333333 |
| p07         | a museum object from Bahrain              | bahrain_museum_objects | en         | local          |                          40 |                0 |              0.4 |               0.3 |     0.05      |         0.075  | 0.5      |
| p08         | a Dilmun artifact in a museum             | bahrain_museum_objects | en         | local          |                          40 |                0 |              0   |               0.2 |     0         |         0.05   | 0.166667 |
| p09         | the exterior of a national museum         | architecture_sites     | en         | generic        |                          12 |                1 |              0.2 |               0.3 |     0.0833333 |         0.25   | 1        |
| p10         | the interior of a museum gallery          | museum_interior        | en         | generic        |                          30 |                1 |              1   |               0.9 |     0.166667  |         0.3    | 1        |
| p11         | مخطوطة عربية                              | manuscript_calligraphy | ar         | arabic         |                          40 |                0 |              0   |               0.1 |     0         |         0.025  | 0.166667 |
| p12         | فخار إسلامي                               | pottery_ceramics       | ar         | arabic         |                          80 |                1 |              0.6 |               0.7 |     0.0375    |         0.0875 | 1        |
| p13         | تمثال في متحف                             | sculptures_statues     | ar         | arabic         |                          40 |                0 |              0   |               0   |     0         |         0      | 0        |
| p14         | متحف البحرين الوطني                       | bahrain_museum_objects | ar         | arabic         |                          40 |                1 |              0.2 |               0.1 |     0.025     |         0.025  | 1        |
| p15         | داخل المتحف                               | museum_interior        | ar         | arabic         |                          30 |                0 |              0   |               0   |     0         |         0      | 0        |