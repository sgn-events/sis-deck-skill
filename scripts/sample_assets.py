"""Manifest of the SGN sample assets shipped with the design handoff.

These files are rights-restricted: the speaker portraits, media logos and event
lockups are cleared for SGN event marketing only. The generator refuses to place
any of them in a deck unless the content explicitly declares
`meta.sampleAssets: "sgn-internal"` — which only examples/content.json does.

Matching is on the path relative to the assets root, on the bare filename, and
on the SHA-256 of the file contents — so neither renaming a directory nor
renaming the file itself slips a restricted face past the check.
"""

import hashlib

SAMPLE_ASSETS = (
    "media/bein.png",
    "media/canal-plus.png",
    "media/fichier-44.png",
    "media/financial-times.png",
    "media/gazzetta.png",
    "media/layer.png",
    "media/logo-10.png",
    "media/logo-13.png",
    "media/logo-1431.png",
    "media/logo-1470.png",
    "media/logo-1503.png",
    "media/logo-1505.png",
    "media/logo-1506.png",
    "media/logo-1507.png",
    "media/logo-vector2.png",
    "media/logoblanc.png",
    "media/logotheque-bandeau.png",
    "media/press/press-business-insider.png",
    "media/press/press-podcast.png",
    "media/press/press-sbb.png",
    "media/press/press-tradingview.png",
    "media/rmc.png",
    "media/sbc.png",
    "photos/fireside-marc-lasry.jpg",
    "photos/hotel-crillon.jpg",
    "photos/roland-garros.jpg",
    "photos/sportgen-panel.jpg",
    "sgn-investment-summit-black.png",
    "sgn-investment-summit-white.png",
    "speakers/adnan-khalef.jpg",
    "speakers/adriana-crovetto.jpg",
    "speakers/andy-marston.jpg",
    "speakers/antonio-cacorino.jpg",
    "speakers/arjun-kapur.jpg",
    "speakers/arnaud-caudoux.jpg",
    "speakers/bex-smith.jpg",
    "speakers/charlie-stebbings.jpg",
    "speakers/danny-menken.jpg",
    "speakers/kushaan-ahuja.jpg",
    "speakers/kyang-yung.jpg",
    "speakers/marc-lasry.jpg",
    "speakers/mark-wyatt.jpg",
    "speakers/mofses-kechichian.jpg",
    "speakers/paolo-della-rovere.jpg",
    "speakers/sgn-caroline-garcia.jpg",
    "speakers/sgn-david-coulthard.jpg",
    "speakers/sgn-dominic-thiem.png",
    "speakers/sgn-eno-polo.png",
    "speakers/sgn-kameryn-stanhope.jpg",
    "speakers/sgn-nfl-speaker.jpg",
    "speakers/sgn-patrick-mouratoglou.jpg",
    "speakers/sgn-romy-gai.png",
    "speakers/sgn-speaker-tbd.jpg",
    "speakers/sgn-teodora.jpg",
    "sportgen-logo-black.png",
)

SAMPLE_BASENAMES = frozenset(p.rsplit("/", 1)[-1] for p in SAMPLE_ASSETS)
SAMPLE_PATHS = frozenset(SAMPLE_ASSETS)

# SHA-256 of each file in the handoff bundle's deck/assets/, so a restricted
# portrait stays recognisable after a rename.
SAMPLE_SHA256 = frozenset((
    "559dfe3561c77cf9ba2a65137a41b14ac3e17645c99452b96d3d6255a86ca1b1",  # media/bein.png
    "adb3caa0de140fd9dabaa90fa6ad8c6efa7efce14c22e7efc84eb7b3f825329c",  # media/canal-plus.png
    "3bcd1267cfa91e4de30ba7d935a2fa5431f7d1df534e51b54b35afce7f9905e3",  # media/fichier-44.png
    "8ffda869fdd6bda118a9426582245a98a2f3f165a3094e3e0c5132e8f85b6022",  # media/financial-times.png
    "e4a763823469933cb842eb29575e192fe42072439d70e400e98542cd8d3d6002",  # media/gazzetta.png
    "b952c4e3640df965fb5a7f0e7ddc738c33a52471a7da20c1d421d0b8cd0df1b7",  # media/layer.png
    "f539023ea2f8b39ce099166924124a4a3956e3d18653a32b5b5da4f75c23925e",  # media/logo-10.png
    "b8e2dc8f0d6b9b7d3b78aa12124a23a3fd9765317475b7abed24838fe286139d",  # media/logo-13.png
    "fd4b7b194a5e23c9aec972a399895559037f01fb533c83e57f94c1b44b026bbd",  # media/logo-1431.png
    "81a4ee70629290c60c98e30d0522f67dc0a2d64ba51bddbd949acab5cf9c459b",  # media/logo-1470.png
    "4a7d7b5833b50f978d9963f7bcbcf590a45d4e725f8b8c4c56608cf1eee29297",  # media/logo-1503.png
    "e76a3aac04397f5657868451fec83b97538a4cfb88d06e38ad17a2dfcbc77718",  # media/logo-1505.png
    "db05dace7d177c9cc8df2d2606d49248bbdcd1d979a3a293fc2652fd2f2b7ec9",  # media/logo-1506.png
    "58bcb9fd873a332c397734baec8bcdfbe10c7b7a912588ba60beb8d110907f74",  # media/logo-1507.png
    "e91522f58b13e17af7575800b706867ce8a46204f6bf5eacf97543e94da84a7f",  # media/logo-vector2.png
    "0644982fcd203cf2818b8858079eef3fb2b89484ab76b98aa6387ac17b9c7e10",  # media/logoblanc.png
    "bb53ae8aae428c54f7b4de8cce5af9e6c6d8a6f9c55ab73451fd2b064fad7751",  # media/logotheque-bandeau.png
    "00246c2307d6b66db0f956e5d24be20016738fd2ba0f14b5a7c487e43a1a7d02",  # media/press/press-business-insider.png
    "6ab1b99b569d7f8c79af0d3c83f084280ca92372aa6fa6f81e4c3df302f4e13e",  # media/press/press-podcast.png
    "a91f7cd7b816e00177e0e0d5deb4333b77f2ba99ab84f83afe3ed0437b8da5d4",  # media/press/press-sbb.png
    "2315bc781928aff5efdc190d513b2cb9fab665bf29959a3fe5a799529e0772d4",  # media/press/press-tradingview.png
    "e860a8e2518028bb9694b10df9c148614700b0c40da1358ce54ab00d240e179e",  # media/rmc.png
    "febb058c6b28ae90ab43658c5697b2ad4ba0ba54f889a843d5d9b6261f4e4721",  # media/sbc.png
    "9fb5bd70ee5e8a5a31e905a044cfd00813062058ee8950ce070d031cce40f522",  # photos/fireside-marc-lasry.jpg
    "38ca92870e7998aa13889583d6dd576ad065d0e5e9cbf8502ee27f41c73d9781",  # photos/hotel-crillon.jpg
    "41de5d57191d2c658c9d048c595180599fc5823874f379bf0237dda759bbe7c6",  # photos/roland-garros.jpg
    "73bde248f73aa929a418a58a761f9ba1487e3dbbeb7c7cf32b90865fc35ca43e",  # photos/sportgen-panel.jpg
    "ad548292f4f02104371c611fbf1c600c1ad46e077335211f46585e772a84c014",  # sgn-investment-summit-black.png
    "09f48dcb53c66d1fb910704d9429d4be082403df28949c00f6ee281cf1a35c31",  # sgn-investment-summit-white.png
    "d456e9e6ddc8e13705a8295f9277a42026a987a1a01b1edbdb6b26f307f95edc",  # speakers/adnan-khalef.jpg
    "a9c0294e50ee1421b7ee3e427ced3076e5dfcab148b3e2ce6ab05af9aba1df8e",  # speakers/adriana-crovetto.jpg
    "ad7bf6c7024a8ad0dadd024e78c1a57d9b761aa4115633b0ffede7af9216c712",  # speakers/andy-marston.jpg
    "a85bd2bb5e49f0b6d34d60320f2854a907c2abf88afaf1aa97ec0cdad7c0b03d",  # speakers/antonio-cacorino.jpg
    "35e8f45a1c9836d4bb1972bacbcad3c0f4ab0dac0aebfa624a458b4a9a908265",  # speakers/arjun-kapur.jpg
    "6e43a743569e5566f1a626cefea305f204928f7bbb3b6baf56e8ba0be94193ef",  # speakers/arnaud-caudoux.jpg
    "e80dfab56af132252b80efecb8a8f19afa6fb7f528df1799416588c68a391f17",  # speakers/bex-smith.jpg
    "a1b445db7fdac702070f5f9247973eea811a7cd6341d98bacf2656272971f26a",  # speakers/charlie-stebbings.jpg
    "e08e12c010439f4e2e0b0aebf37790f7d524bbd3382cb8fb138dc05024c78721",  # speakers/danny-menken.jpg
    "e34d8055eb2d3572a686b749102bd31214699540a71962ae45e1c680308e2348",  # speakers/kushaan-ahuja.jpg
    "ef0cafdb4418b3a57968e330ae1e05d6bda0c799a043caffcf4a06966f7999e4",  # speakers/kyang-yung.jpg
    "7b0b2f25de339cd86063cb7bf6f7693bda21e9ff3f9b2ba6ab858dcb2f9154a7",  # speakers/marc-lasry.jpg
    "69dbb40414b350273dfbff122c3756e484395ecf8b09a659907fef1939339322",  # speakers/mark-wyatt.jpg
    "c378f6de11a0bf1b486f420bc6c785caa62dc65b42b17580e05cf80c3ed02e11",  # speakers/mofses-kechichian.jpg
    "68456611ac3ee27abd6b13af89d9393c0180190953f8472a41019bf9da430ee6",  # speakers/paolo-della-rovere.jpg
    "9fd5f0f1a793667e3e420ece83d6c1f4911373167a61440df0946dbc5362b867",  # speakers/sgn-caroline-garcia.jpg
    "e24156660b05f113844d1bcf93f6f51d80daf477f29c238104b147863b95186c",  # speakers/sgn-david-coulthard.jpg
    "b0a3d36c8df101dc81124c25d788b01782d4a5ecbd78bef37937d95c2b9ddd92",  # speakers/sgn-dominic-thiem.png
    "1f36a6c698a6725375f92522cda916d49c246e2f5eb47464acc0fb36ae07d935",  # speakers/sgn-eno-polo.png
    "dd26ce2d371fb7faaecebee2968bc0c6aaea99fd1ec083aab3fbfd49371a373a",  # speakers/sgn-kameryn-stanhope.jpg
    "70e5c8710220843d09a4e7f1c78642d55b9705d1816ce7727fc45e3ad2c83d3c",  # speakers/sgn-nfl-speaker.jpg
    "c7fcefe142c38ad73fde2682c39862959368a3d52e7563d862a6ef779345a817",  # speakers/sgn-patrick-mouratoglou.jpg
    "278c2f446b7f0579e1a0abf1067bd5a0996cd9e6b71fd7235ae5165644b73ccf",  # speakers/sgn-romy-gai.png
    "0577c550b12c14d5d5d205bc87ce28a94d9fc4c604d76eaf7ac0fdde6d09e865",  # speakers/sgn-speaker-tbd.jpg
    "30ab1b166b6c2086865d9e0318036e00e8af126c22ea023b3911f758366cd2a3",  # speakers/sgn-teodora.jpg
    "6422171aa2d0a57d13888ad871c27ede20077f5a066e830ed7093e9ccc919720",  # sportgen-logo-black.png
))


def is_sample_asset(rel_path: str, data: bytes | None = None) -> bool:
    """True if this names — or *is* — one of the restricted SGN sample files."""
    norm = rel_path.replace("\\", "/").lstrip("./")
    if norm in SAMPLE_PATHS or norm.rsplit("/", 1)[-1] in SAMPLE_BASENAMES:
        return True
    return data is not None and hashlib.sha256(data).hexdigest() in SAMPLE_SHA256
