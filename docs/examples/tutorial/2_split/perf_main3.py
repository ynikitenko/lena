import cProfile

from main3 import main


if __name__ == "__main__":
    cProfile.run("main()") #, "perf.txt")
    # 1.015 s of total 1.115 s
    # is spent on latex_to_pdf, 10 events analysed
