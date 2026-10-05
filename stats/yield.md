# Yield: crawled vs unique, per source

How many postings each source returns, and how many of those are actually new.

This is the number we most wanted when we were choosing what to integrate, and the one
nobody publishes. A source that returns 100k results per cycle of which 3% are new costs
you 100k requests worth of rate limit for 3k postings.

**Found** is every posting returned by the source across all runs. **Unique** is the subset
that was not already in our store. **Yield** is unique/found.

Measured across 60,520 production crawl runs since 2026-03-18.
Figures as of 2026-07-23; live totals at https://kitsuno.ai/stats

| Source | Found | Unique | Yield | Runs | Last run |
|---|---:|---:|---:|---:|---|
| [ATS Direct (Greenhouse / Lever / Ashby / Recruitee / SmartRecruiters)](../sources/ats-direct.yml) | 19,039,517 | 6,347,397 | 33.3% | 1,822 | 2026-07-23 |
| [Jobs.ch](../sources/jobs-ch.yml) | 2,328,810 | 1,237,123 | 53.1% | 2,582 | 2026-07-23 |
| [NoFluffJobs](../sources/nofluffjobs.yml) | 2,024,247 | 1,772,188 | 87.5% | 302 | 2026-07-23 |
| [Adzuna](../sources/adzuna.yml) | 1,423,707 | 1,107,253 | 77.8% | 2,849 | 2026-07-23 |
| [Indeed](../sources/indeed.yml) | 849,139 | 239,648 | 28.2% | 3,556 | 2026-07-23 |
| [Arbeitnow](../sources/arbeitnow.yml) | 798,619 | 428,944 | 53.7% | 2,671 | 2026-07-23 |
| [France Travail](../sources/francetravail.yml) | 318,715 | 291,840 | 91.6% | 796 | 2026-07-23 |
| [Net-Empregos](../sources/netempregos.yml) | 302,000 | 184,300 | 61.0% | 302 | 2026-07-23 |
| [Reed](../sources/reed.yml) | 270,423 | 201,888 | 74.7% | 873 | 2026-07-23 |
| [RemoteOK](../sources/remoteok.yml) | 266,955 | 140,523 | 52.6% | 2,740 | 2026-07-23 |
| [Jobicy](../sources/jobicy.yml) | 237,700 | 142,067 | 59.8% | 2,440 | 2026-07-23 |
| [The Muse](../sources/themuse.yml) | 225,698 | 159,592 | 70.7% | 1,084 | 2026-07-23 |
| [Platsbanken](../sources/platsbanken.yml) | 223,852 | 198,839 | 88.8% | 789 | 2026-07-23 |
| [LinkedIn](../sources/linkedin.yml) | 203,000 | 46,238 | 22.8% | 2,388 | 2026-07-23 |
| [Himalayas](../sources/himalayas.yml) | 134,049 | 80,843 | 60.3% | 2,313 | 2026-07-23 |
| [WeWorkRemotely](../sources/weworkremotely.yml) | 97,557 | 62,151 | 63.7% | 1,908 | 2026-07-23 |
| [Working Nomads](../sources/working-nomads.yml) | 87,521 | 52,073 | 59.5% | 2,367 | 2026-07-23 |
| [The Hub](../sources/thehub.yml) | 82,176 | 79,339 | 96.5% | 1,357 | 2026-07-23 |
| [NAV (Arbeidsplassen)](../sources/nav.yml) | 81,792 | 73,848 | 90.3% | 675 | 2026-07-23 |
| [ReliefWeb Jobs](../sources/reliefweb.yml) | 80,707 | 20,485 | 25.4% | 1,585 | 2026-07-23 |
| [Remotive](../sources/remotive.yml) | 66,671 | 38,037 | 57.1% | 2,520 | 2026-07-23 |
| [Bundesagentur für Arbeit (Arbeitsagentur)](../sources/arbeitsagentur.yml) | 64,090 | 34,476 | 53.8% | 1,056 | 2026-07-23 |
| [Google X-ray (ATS meta-source)](../sources/google-xray.yml) | 61,138 | 41,992 | 68.7% | 2,072 | 2026-07-23 |
| [Moovijob](../sources/moovijob.yml) | 60,107 | 56,336 | 93.7% | 1,355 | 2026-07-23 |
| [Jooble](../sources/jooble.yml) | 54,459 | 30,368 | 55.8% | 2,723 | 2026-07-23 |
| [CV.online (CV.ee / CV.lv / CVonline.lt)](../sources/cvonline.yml) | 53,760 | 30,147 | 56.1% | 299 | 2026-07-23 |
| [Public Jobs CH](../sources/publicjobs-ch.yml) | 51,400 | 40,978 | 79.7% | 639 | 2026-07-23 |
| [Pracuj.pl](../sources/pracuj.yml) | 47,450 | 34,928 | 73.6% | 318 | 2026-07-23 |
| [Úřad práce ČR (Czech Labour Office)](../sources/uradprace-cz.yml) | 46,609 | 46,592 | 100.0% | 85 | 2026-07-23 |
| [IamExpat](../sources/iamexpat.yml) | 43,079 | 31,703 | 73.6% | 317 | 2026-07-23 |
| [Karriere.at](../sources/karriere-at.yml) | 42,787 | 31,635 | 73.9% | 326 | 2026-07-23 |
| [Devex](../sources/devex.yml) | 32,583 | 25,382 | 77.9% | 1,163 | 2026-07-23 |
| [DevITjobs UK](../sources/devitjobs-uk.yml) | 27,653 | 24,777 | 89.6% | 1,384 | 2026-07-23 |
| [German Tech Jobs](../sources/germantechjobs.yml) | 27,614 | 22,595 | 81.8% | 1,629 | 2026-07-23 |
| [DevITjobs.com (US)](../sources/devitjobs-us.yml) | 27,400 | 24,221 | 88.4% | 1,343 | 2026-07-23 |
| [Tecnoempleo](../sources/tecnoempleo.yml) | 27,030 | 20,944 | 77.5% | 301 | 2026-07-23 |
| [DevITjobs FR](../sources/devitjobs-fr.yml) | 22,117 | 19,873 | 89.9% | 1,329 | 2026-07-23 |
| [DevITjobs NL](../sources/devitjobs-nl.yml) | 19,173 | 18,192 | 94.9% | 1,203 | 2026-07-23 |
| [Swiss Dev Jobs](../sources/swissdevjobs.yml) | 18,807 | 17,248 | 91.7% | 1,357 | 2026-07-23 |
| [job-room.ch (RAV / SECO)](../sources/job-room.yml) | 18,196 | 8,293 | 45.6% | 124 | 2026-07-23 |
| [DevJob.ro](../sources/devjob-ro.yml) | 17,336 | 15,917 | 91.8% | 1,114 | 2026-07-23 |
| [Prace.cz](../sources/prace-cz.yml) | 14,439 | 14,407 | 99.8% | 84 | 2026-07-23 |
| [Dice](../sources/dice.yml) | 14,053 | 9,400 | 66.9% | 1,412 | 2026-07-23 |
| [Profession.hu](../sources/profession-hu.yml) | 13,436 | 13,304 | 99.0% | 224 | 2026-07-23 |
| [Profesia.sk](../sources/profesia-sk.yml) | 4,777 | 4,445 | 93.1% | 81 | 2026-07-23 |
| [80,000 Hours Job Board](../sources/80000hours.yml) | 4,003 | 2,532 | 63.3% | 651 | 2026-07-23 |
| [Hipo.ro](../sources/hipo.yml) | 12 | 0 | 0.0% | 12 | 2026-07-18 |
| **Total** | **29,956,363** | **13,525,301** | **45.2%** | | |

## How to read this

**High volume, low yield** (ats-direct 33%, indeed 28%, linkedin 23%). These are
re-read surfaces: the same postings persist across cycles, so most of what comes
back you already have. Worth running, but budget for dedup on a stable posting id
and do not size your rate limit off the found column.

**High volume, high yield** (nofluffjobs 88%, netempregos 61%, adzuna 78%). Real
churn. These are the sources where crawling more often actually gets you more.

**Low volume, high yield** (moovijob 94%, thehub 97%, prace-cz ~100%). Small or
recently-added boards. A near-100% figure usually means the source has not yet
been running long enough to see its own listings age out, so treat it as
provisional rather than as evidence of a uniquely fresh board.

Yield is not quality. A source can return 100% unique postings that are all
irrelevant to your users. It tells you what a crawl costs, not what it is worth.
