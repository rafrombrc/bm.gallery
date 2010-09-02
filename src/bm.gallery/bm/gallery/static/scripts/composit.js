<!-- Engage cloaking device...

// composIt script by spanky 2001
function composIt(n,d,tld,sbj) {
    var ext = ".com";
    if (tld) { ext = "." + tld; }
    if (d) { d = d + ext; } else { d = "burningman" + ext; }
    var addr = "mailto:" + n + "@" + d;
    if (sbj) { addr = addr + "?subject=" + sbj; }
    location = addr;
    return false;
}

// disengage...  -->
