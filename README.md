# aiofetch
(async) comic image fetcher for http://www.cartoonmad.com/

# library required:
  see [requirements.txt](https://github.com/LFLab/aiofetch/blob/master/requirements.txt)

# usage
use `python aiofetch.py -h` to get usage.  something like that:
```
python aiofetch.py http://www.cartoonmad.com/comic/1300.html -d bleach -l 100
```

# performance
```
$ python aiofetch.py http://www.cartoonmad.com/comic/4387.html -d slime > history.log
=== program start at 2017-08-07 00:37:42.402054 ===
=== tasks done at 2017-08-07 00:38:30.575810 ===
retry for 75 page(s) at 2017-08-07 00:38:30.576810
=== program end at 2017-08-07 00:38:54.491178 ===
```
total 781 files, 210MB