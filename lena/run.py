from __future__ import print_function


def run(seq, args, **kwargs):
    # seems I can't import it in the heading,
    # because it imports other modules and causes
    # cyclic dependencies
    import lena.output

    results = seq()
    if "--json" in args:
        import json
        json_encoder = lena.output.JSONEncoder()
    else:
        json_encoder = None
    for result in results:
        if json_encoder:
            try: 
                result = json.JSONEncoder().encode(result)
            except TypeError:
                result = json_encoder.encode(result)
        print(result)
        # return result
