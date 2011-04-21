import datetime
import sys
import time

import pylast
import simplejson

config = simplejson.load(open("config.json", "r"))
def get_network_connection():
    return pylast.LastFMNetwork(api_key=config["API_KEY"],
                                api_secret=config["API_SECRET"]);

def parse_args():
    username, start_date_str, end_date_str = sys.argv[1:4]

    def ts_from_str(s):
        return unicode(int(time.mktime(datetime.datetime.strptime(s, "%Y%m%d").timetuple())))

    return username, ts_from_str(start_date_str), ts_from_str(end_date_str)

def get_top_tracks(nc, username, start_ts, end_ts):
    user = pylast.User(username, nc)

    # get available date ranges
    all_dates = user.get_weekly_chart_dates()

    # find all tuples that fall somewhere between start/end dates
    tuples_to_check = [ tpl for tpl in all_dates if start_ts < tpl[1] and end_ts > tpl[0] ]

    # pull top tracks from each ts pair
    top_track_sets = [ user.get_weekly_track_charts(start, end) for start,end in tuples_to_check ]

    # merge duplicate tracks
    top_tracks = {}
    for seq in top_track_sets:
        for topitem in seq:
            key = (topitem.item.get_artist(), topitem.item.get_title())
            if key in top_tracks:
                old_weight = top_tracks[key].weight
                top_tracks[key] = pylast.TopItem(top_tracks[key].item, top_tracks[key].weight + topitem.weight)
            else:
                top_tracks[key] = topitem

    return sorted(top_tracks.values(), key=(lambda x: x. weight), reverse=True)

def trim_by_weight(top_tracks):
    # trim down the tracks, keeping the top 50% by weight after knocking out the single plays
    nonsingular_top_tracks = [ track for track in top_tracks if track.weight > 1 ]
    weight_to_keep = 0.50
    total_weight = sum([ track.weight for track in nonsingular_top_tracks ])

    weight = 0
    trimmed = []
    for track in nonsingular_top_tracks:
        trimmed.append(track)
        weight += track.weight
        if weight > weight_to_keep * total_weight:
            break
    return trimmed

def main():
    args = parse_args()
    nc = get_network_connection()
    top_tracks = get_top_tracks(nc, *args)

    trimmed = trim_by_weight(top_tracks)
    print "pulled", len(top_tracks), "trimmed to", len(trimmed)

    for t in trimmed:
        artist = t.item.get_artist().get_name()
        title = t.item.get_title()
        print "%s - %s (%d)" % (artist, title, t.weight)

if __name__ == "__main__":
    main()
