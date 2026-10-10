# Held-out block: addendum on the exports, written before the analysis

Written 2026-10-02 and completed 2026-10-10. No result of the analysis has been computed or
read: no false alarm, gate opening, rate or blocked share of a block day. For every file
the block run reads, this addendum gives its SHA-256, its number of rows and its first and
last window, as `heldout_block_protocol.md` asks ("After the export, before the analysis").
It is committed and pushed before the analysis. All three parts are here, so the block
holds its 14 days in full.

The rows and windows were taken from the files without reading any count. A window is a
5-minute bin, so a full day holds 288.

**What was seen at export.** When a query runs, Metabase shows the first rows of its result
on screen before the download. The person who exported the parts glanced at a few of those
rows without analyzing them. This departs from the metrics addendum's rule that results are
not previewed. Those rows are raw counts of clients per host, window and fingerprint. No
false alarm, gate opening or other result of the analysis appears there, since those exist
only once the run computes them.

## Part 1: 2026-09-26 to 09-30

Exported on 2026-10-01 at 12:49 UTC, the time in each file name, with the held-out day's
queries and only their date range changed. The drive was not at hand, so the files were
downloaded to a local folder outside the repository and then put on the drive. On
2026-10-02 they were moved into the part's directory, which left their SHA-256 unchanged.

| File, in `block2/2026-09-26_2026-09-30/` | Export | SHA-256 | Rows | Windows | First and last window (UTC) |
|---|---|---|---:|---:|---|
| `query_result_2026-10-01T12_49_33.28181Z.json` | E3 | `d19b2f99d75e4f5b778f73147ede4a49c7df467a8cf17115a4896584f0943254` | 211,500 | 1,440 | 09-26 00:00 to 09-30 23:55 |
| `query_result_2026-10-01T12_49_55.580725Z.json` | E4 | `1234d34d0ff7e8bb5116e1c656c1e804c286c60de73c58664bd3d889bf12a9b2` | 10,389 | 1,440 | 09-26 00:00 to 09-30 23:55 |

Both files hold the five days in full, since 1,440 windows is 5 × 288. Both are far below
Metabase's download limit of about a million rows, so neither was cut short.

On 2026-10-02 a blind check loaded the part with the loader at `05ccc0e`, as the block run
will, and printed no count (`scripts/block_part_check.py`). The windows parse as UTC, no
host-window is shared with the history, and each of E1–E4 holds all 1,440 windows in both
exports.

## Part 2: 2026-10-01 to 10-05

Exported on 2026-10-07 at 18:55 UTC, the time in each file name, with the same queries and
only their date range changed. The files were downloaded to a local folder outside the
repository, then put on the drive in a directory outside the block's. On 2026-10-07 they
were moved into the part's directory, which left their SHA-256 unchanged.

| File, in `block2/2026-10-01_2026-10-05/` | Export | SHA-256 | Rows | Windows | First and last window (UTC) |
|---|---|---|---:|---:|---|
| `query_result_2026-10-07T18_55_00.824187Z.json` | E3 | `6ead88500b466cf6c7405d5924856cd0f52262e0a3d9b3e080c0b729ca433ee3` | 216,891 | 1,440 | 10-01 00:00 to 10-05 23:55 |
| `query_result_2026-10-07T18_55_20.574001Z.json` | E4 | `7315d72c954377f2095347c5c765582e52d31e0ee157054b53a9368d8dee1cbd` | 10,637 | 1,440 | 10-01 00:00 to 10-05 23:55 |

Both files hold the five days in full, far below Metabase's download limit. The same day,
the blind check found the windows in UTC, no host-window shared with the history or with
part 1, and all 1,440 windows for each of E1–E4 in both exports.

## Part 3: 2026-10-06 to 10-09

Exported on 2026-10-10 at 14:53 UTC, the time in each file name, with the same queries and
only their date range changed. The files were downloaded to a local folder outside the
repository, then put on the drive in a directory outside the block's. The same day they
were moved into the part's directory, which left their SHA-256 unchanged.

| File, in `block2/2026-10-06_2026-10-09/` | Export | SHA-256 | Rows | Windows | First and last window (UTC) |
|---|---|---|---:|---:|---|
| `query_result_2026-10-10T14_53_14.628042Z.json` | E3 | `e43d8ad9b265c4af7ff938870b42ea279308710aeffd4ac48903ba8ec7a12fe2` | 188,653 | 1,152 | 10-06 00:00 to 10-09 23:55 |
| `query_result_2026-10-10T14_53_34.416865Z.json` | E4 | `61ec9fef793f04eb165f1109258fe278fb988d8b3e54d9a024d79c2289fa7a77` | 8,194 | 1,152 | 10-06 00:00 to 10-09 23:55 |

Both files hold the four days in full, since 1,152 windows is 4 × 288, far below Metabase's
download limit. The same day, the blind check found the windows in UTC, no host-window
shared with the history or with parts 1 and 2, and all 1,152 windows for each of E1–E4 in
both exports.

## History copies

The block directory holds copies of the paper's nine days, so that the paper's runs never
read the block. Each copy's SHA-256 equals that of the paper's file (checked 2026-10-02).

| File, in `block2/` | SHA-256 |
|---|---|
| `2026-09-17_2026-09-24/query_result_2026-09-25T00_23_30.078892Z.json` | `9e54a5c9de8b69ddbdb7f9e9d506790ba12cd681fdb6eedc548dae79d988886e` |
| `2026-09-17_2026-09-24/query_result_2026-09-25T00_23_49.42169Z.json` | `58e12a2fdee868851d5b007cc034173ac278ef56398469e5b70bb0b54c62eae0` |
| `2026-09-17_2026-09-24/query_result_2026-09-25T00_24_09.533581Z.json` | `99508cf9dcf69105dc8448af593112ac5ae52165fe6adced0f7ed7a615c4b68e` |
| `2026-09-23/query_result_2026-09-24T23_19_17.993129Z.json` | `5c684c53af544f9cf39ec4be089dffb9759142fa019efa92be73a8fdf1ae8a5a` |
| `2026-09-23/query_result_2026-09-24T23_19_38.743599Z.json` | `814998877c0a5f2b6fadafe2b3dee0d291d618938f60393e0c26c3d3b9b60539` |
| `2026-09-23/query_result_2026-09-24T23_52_02.327244Z.json` | `72364f9a6e6172f4b127bdcb7fd70956fd5a1114aba23f203ff2067261e1cc46` |
| `2026-09-23/query_result_2026-09-24T23_52_19.909281Z.json` | `5776a9b3d29eb5ed9630e1e7dbfd1a2bd6a95afdfad3280ee0894761cbe6d113` |
| `2026-09-23/query_result_2026-09-25T00_14_02.193837Z.json` | `7ae3a81a1bff685052a3d73bea509327ef3f178d00505fcc8cc5eaa3c1d9c452` |
| `2026-09-25/query_result_2026-09-26T02_34_48.2708Z.json` | `b1d1737458ea6de3f07152cbee9752b0c5910f71ae3f602ac7628ef137504bf1` |
| `2026-09-25/query_result_2026-09-26T02_35_08.226479Z.json` | `2520b8118fccf722f0000a0473a76ecd694175770f9eef87851216f54974fdf8` |

## Order of events

- 2026-09-28: the protocol, pushed in commit `05ccc0e`.
- 2026-10-01, 12:34 UTC: the metrics addendum, written.
- 2026-10-01, 12:49 UTC: part 1, exported.
- 2026-10-01, 12:54 UTC: one sentence added to the metrics addendum, on downloading a part
  when the drive is not at hand.
- 2026-10-02: the metrics addendum's additions on metric 10, the report script and metric 7.
- 2026-10-07, 18:55 UTC: part 2, exported.
- 2026-10-10, 14:53 UTC: part 3, exported.
- Before any count is read: this addendum and the metrics addendum, committed and pushed
  together. The push time on GitHub dates them.
