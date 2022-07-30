def profile(func, *args, **kwargs):
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        try:
            func(*args, **kwargs)
        except SystemExit:
            pass

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename='stats.prof')


if __name__ == '__main__':
    import main
    profile(main.main)
