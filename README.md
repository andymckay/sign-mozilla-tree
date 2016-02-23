This script will run sign an addon or run through a directory finding addons that it needs to sign. It might be useful if you wanted to sign all the add-ons in mozilla-central for example.

You will need a key and secret from the AMO server which you then need to export, for example:

```
    export AMO_SIGNING_KEY=key
    export AMO_SIGNING_SECRET=secret
```

You can then run it on a file or a directory:

```
    python sign-addon.py ~/sandboxes/gecko
```

It will find and sign all the add-ons in that directory if possible.

It then:
* checks if the add-on needs to be signed
* tries to find its id and version
* sees if its on the server already and if you have access
* signs it
* waits for the signed add-on and moves it over to its place

```
    python unique-addon.py --print ~/sandboxes/gecko
```

Print sill find all the non-unique version id combinations for all unsigned add-ons.

```
    python fix-addon.py --fix ~/sandboxes/gecko addon@id
```

Will attempt to bump the version in each add-on so they aren't unique. You will want to run print afterwards to check there are no conflicts.
