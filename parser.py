import logging
import re

import mwparserfromhell as mwp

logger = logging.getLogger("talk-parser.topic_extractor")

# 21:11, 17 July 2013 (UTC)
TIMESTAMP_RE = re.compile(r"[0-9]{2}:[0-9]{2}, [0-9]{1,2} [^\W\d]+ [0-9]{4} \(UTC\)")

USER_TITLE = re.compile(r"(User_talk|User):(=?P<title>.+)", re.I)

"""
mwp.nodes.Argument
          Comment
          ExternalLink
          HTMLEntity
          Heading
          Tag
          Template
          Text
          Wikilink
"""

class Topic(list):

    def __init__(self, title, items=None):
        super().__init__(items or [])
        self.title = title

class Post(list):

    def __init__(self, nodes=None, user_text=None, timestamp=None):
        super().__init__(nodes or [])
        self.user_text = user_text
        self.timestamp = timestamp

# Extracts topics from a provided piece of wikimarkup
class TopicExtractor:

    def __init__(self, signature_timestamp_re=TIMESTAMP_RE,
                       min_topic_heading=2):
        self.signature_timestamp_re = signature_timestamp_re
        self.min_topic_heading = int(min_topic_heading)

    def extract(self, text):
        logger.info("Extracting from text.")
        wikicode = mwp.parse(text)
        return self.extract_nodes(wikicode.nodes)

    def extract_nodes(self, nodes, pos=0):
        """
        Extracts topics from nodes.  Returns a generator of
        `Topic`
        """
        logger.info("Extracting from nodes beginning with: {0}" \
                    .format(str(nodes[pos:])[:100] + "..."))

        while pos < len(nodes):
            node = nodes[pos]
            if isinstance(node, mwp.nodes.Tag):
                # A tag can contain any amount of the page and needs
                # to be treated like a first-order thing at this level.
                tag = node
                if tag.contents is not None:
                    for pos, topic in self.extract_nodes(tag.contents.nodes):
                        yield topic
            elif isinstance(node, mwp.nodes.Heading):
                # We ran into a header.  If the header is small enough
                # then we suppose we ran into the beginning of a topic.
                heading = node
                if heading.level >= self.min_topic_heading:
                    pos, topic = self._extract_topic(nodes, pos)
                    yield topic
            else:
                # We ran into something that isn't a header or a tag.
                pass

            pos += 1

    def _extract_topic(self, nodes, pos):
        """
        Extracts a single topic from nodes.  Returns a single
        topic.  Topic may lack content if there's nothing but a header
        """
        logger.info("Extracting from topic beginning with: {0}" \
                    .format(str(nodes[pos:])[:100] + "..."))

        heading = nodes[pos]
        pos += 1

        topic = Topic(heading.title)

        while pos < len(nodes):

            if isinstance(nodes[pos], mwp.nodes.Heading):
                next_heading = nodes[pos]
                if next_heading.level < heading.level:
                    # We've reached a sub-header.
                    topic.append(self._extract_topic(nodes, pos))
                else:
                    # Same level or greater header.  We're done here.
                    return pos, topic
            else:
                post = self._extract_post(nodes, pos)
                topic.append(post)

            pos += 1

        return pos, topic

    def _extract_post(self, nodes, pos):
        """
        Extracts a post from the wiki code.
        """
        logger.info("Extracting from post beginning with: {0}" \
                    .format("".join(str(n) for n in nodes[pos:])[:100] + "..."))
        post = Post()

        while pos < len(nodes):
            node = nodes[pos]
            if isinstance(node, mwp.nodes.Heading):
                # Can't read past a header
                return pos, post
            elif self.signature_timestamp_re.search(str(node)):
                # Found a signature!
                timestamp = self.signature_timestamp_re.search(str(node))
                post.timestamp = timestamp
                post.user_text = self._last_user_linked(nodes, pos)

                return pos, post
            else:
                post.append(node)

            pos += 1

        return pos, post


    def _last_user_linked(self, nodes, pos=None):
        """
        Gets the most recent link to User or User_talk before `pos`
        """
        pos = pos or len(nodes)-1

        for i in range(1, pos+1):
            back_pos = pos - i
            node = nodes[back_pos]

            if isinstance(node, mwp.nodes.Wikilink):
                wikilink = node
                match = USER_TITLE.match(str(wikilink.title))
                if match: return self._normalize_user_text(match.group('title'))
            elif isinstance(node, mwp.nodes.Tag):
                tag = node
                if tag.contents is not None:
                    user_text = self._last_user_linked(tag.contents.nodes)
                    if user_text is not None: return user_text

            elif self.signature_timestamp_re.search(str(node)):
                break

        return None

    def _normalize_user_text(self, title):
        """
        Extracts the user_text from a link.
        """
        return title[0].upper() + title[1:].replace("_", " ")


text = """==i want to add a important link, but==

i had tried to add a new link, that is considerable important for this article and the Mycanaean greek article, but, a stupid bot, deleted it several times. i give you the link for your consideration, that i think, and many of us i suppost, is extremely relevant:

[http://www.geocities.com/kurogr/linearb.pdf Glossary of Linear B]  <small>—Preceding [[Wikipedia:Signatures|unsigned]] comment added by [[User:Hans soplopuco|Hans soplopuco]] ([[User talk:Hans soplopuco|talk]] • [[Special:Contributions/Hans soplopuco|contribs]]) 19:54, 29 January 2008 (UTC)</small><!-- Template:Unsigned --> <!--Autosigned by SineBot-->
:Hello Hans, you present us with a problem worse than the Palmer-Boardman dispute. If this pdf were accessed from an allowed source, then I for one think it should be in there, as it seems to be scholarly, taking material from scholarly sources. But you aren't telling us everything. This file is being published from a commercial site selling tourism services. It lists a number of interesting articles but they are not distinguished from the tour guide business. Everywhere you look it is buy this, buy that. I have allowed (every editor has the power to delete except for entire articles) linked articles to stand when published by a business provided you can get to it without going through their website and it does not talk about the business. Not so in this case. Who shall we say published it? Now, if you look at the pdf, there are only a few pages of vocabulary items. The whole dictionary is many pages. So, what the author is doing is offering us a small taste in order to get us interested in his business (or his employer's business). There is no evidence that he is a scholar in the field. I do not know why the man behind the bot (there is one you know) targeted this link but right now I would have to agree with his decision on the ground that it is inextricable from the commercial site. Wikipedia is an encyclopedia not a collection of commercials no matter how appealing to the intellect. That is about the best I can say buddy. If you want to make an issue just keep putting it back on the grounds that you were not given any reasons. Make sure you keep us posted in the discussion here. You need to use the cite web template, which unfortunately will expose the publisher. There is an appeal process but my guess is after a few times back an administrator will take a hand. What does everyone else think? What is the judgement of public opinion such as it is found here? Feel free to chip in, people. Keep the link or no and why?[[User:Botteville|Dave]] ([[User talk:Botteville|talk]]) 02:32, 5 January 2009 (UTC)
:PS. The original link was to a tour guide business. This link is to a personal site, which is just as bad. That means it is not an encyclopedic source. Blogs, personal sites, things of that nature, aren't allowed. Who is that author and what is his claim to authority on Wikipedia?[[User:Botteville|Dave]] ([[User talk:Botteville|talk]]) 02:38, 5 January 2009 (UTC)

==Is Linear B like Chinese or Japanese?==

I would admit that I don't know Linear B.  But if it is as described as "poor compliance with the phonemic principle" and is partly syllabic, with additional logographic signs that are "determinative", or "designational" (yielding "classes", and "types"), it is more like Chinese than Japanese.

The Japanese kana is pure syllabic and forms complete words while kanji (literally, Chinese word) is imported complete word.  The interleaving of kana and kanji serves as word delimiter since Japanese does not have "space" as modern European languages.

A significant numbers of Chinese words are phonemic with determinative, though most of them are poorly compliant with phonemic principle.

To claim that Linear B is like Japanese is to say that Linear B consists of phonemic symbols interleaving with foreign words such as Egyptian hieroglyphs.

-----

I can't read any of the signs on this page.  I think we'd need images for all the signs, since most people viewing this page will not have the appropriate fonts installed. [[User:Pfalstad|Pfalstad]] 05:44, 20 Feb 2005 (UTC)

:I know. Unicode Linear B is hardly supported by any system. If you can find a copyright-free image, or create one yourself, it would be  most welcome [[User:Dbachmann|dab]] <small>[[User_talk:Dbachmann|('''&#5839;'''</small>)]] 09:33, 20 Feb 2005 (UTC)

-----
The conclusion drawn by [[User:Spryom]], ''"that all early civilizations in the eastern mediterannean areas (mainland Greece, Aegean, Cyprus, Crete and Ionian coast) were actually Greek."'', is unwarranted. I adjusted accordingly. Mycenaean-age settlements that show material culture of Mycenaeans suggest Greek-speaking cultures in specific Aegean sites, but I thought that was getting offtopic. --[[User:Wetman|Wetman]] 16:46, 15 July 2005 (UTC)
:I think that my phrase was quite bad and I certainly won't insist on it, but your wording greatly weakens the archaeological significance of the deciphering and doesn't show a united Greek world of the Mycenean times. My view is that more than  "that a Greek-speaking Minoan-Mycenaean culture existed on Crete", the deciphering of Linear B showed a united (at least culturally) Greek world in the area. Evans thought that the Cretans and Myceneans were enemies of different cultures. Linear B showed that they were the same tribe. This also unites them under a common civilization, with the Cypriots and the Ionian coast, where we also know that Linear B and A was used. It appears you're a native english speaker, would you consider another go? --[[User:Spryom|Spryom]] 09:51, 16 July 2005 (UTC)
-----------------
This article needs a lot of work - it should address both issues just raised - and include the link above.

And foremost, it should give dates for Linear B - not just "Late Bronze age" in the date space in the right column.  I know I've seen citations several times regarding these dates.

I personally think Linear B conforms to the statistical requirements of a phonetic alphabet, and I'm certainly not alone in that idea.
LK (UTC)"""

logging.basicConfig(level=logging.INFO)
extractor = TopicExtractor()
list(extractor.extract(text))
