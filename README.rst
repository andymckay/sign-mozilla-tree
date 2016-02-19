This script will run sign an addon or run through a directory finding addons that it needs to sign.

You will need a key and secret from the AMO server which you then need to export, for example:

    export AMO_SIGNING_KEY=key
    export AMO_SIGNING_SECRET=secret

You can then it on a file or a directory:

    python sign-addon.py ~/sandboxes/gecko

It will find and sign all the add-ons in that directory if possible.
