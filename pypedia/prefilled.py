
prefilled_text = """{{#form:action=<nowiki>http://www.pypedia.com/extensions/PyPedia_server/pypdownload.php</nowiki>|method=post|target=_blank|id=header_form|enctype=multipart/form-data}}{{#input:type=hidden|name=article_title|value=@PYPEDIAARTICLENAME@}}{{#input:type=hidden|name=pyp_username|value={{CURRENTUSER}}}}{{#input:type=ajax|value=Fork this article|id=fa}}{{#formend:}}
==Documentation==

Documentation for '''@PYPEDIAARTICLENAMENOUS@'''
[[Category:User]]
[[Category:Algorithms]]
===Parameters===

<!-- DO NOT EDIT HERE! AUTOMATICALLY GENERATED -->
{{#form:action=<nowiki>http://www.pypedia.com/extensions/PyPedia_server/pypdownload.php</nowiki>|method=post|target=_blank|id=parameters_form|enctype=multipart/form-data}}
<p>
{{#input:type=hidden|name=article_title|value=@PYPEDIAARTICLENAME@}}
{{#input:type=hidden|name=pyp_username|value={{CURRENTUSER}}}}
{{#input:type=ajax|value=Run|id=eob}}
{{#input:type=ajax|value=Download code|id=dc}}
{{#input:type=ajax|value=Execute on remote computer|id=eorc}}
{{#formend:}}

<!-- EDIT HERE! -->
<source lang="xml">

<inputs>
</inputs>

</source>
===Return===

===See also===

==Code==

<source lang="py">
def @PYPEDIAARTICLENAME@():
	pass

</source>

==Unit Tests==

<source lang="py">

def uni1():
	return True

</source>

==Development Code==

<source lang="py">
def @PYPEDIAARTICLENAME@():
	pass

</source>

==Permissions==

===Documentation Permissions===

@PYPEDIAUSERNAME@

===Code Permissions===

@PYPEDIAUSERNAME@

===Unit Tests Permissions===

@PYPEDIAUSERNAME@

===Permissions Permissions===

@PYPEDIAUSERNAME@
"""
