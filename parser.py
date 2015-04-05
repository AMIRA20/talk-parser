import mwparserfromhell as mwp
import re

# 21:11, 17 July 2013 (UTC)
TIMESTAMP_RE = re.compile(r"[0-9]{2}:[0-9]{2}, [0-9]{1,2} [^\W\d]+ [0-9]{4} \(UTC\)")

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
        self.title = title
        self.items = items or []

class Post(list):
    
    def __init__(self, nodes=None, user_text=None, timestamp=None):
        super.__init__(self, nodes or [])
        self.user_text = user_text
        self.timestamp = timestamp

# Extracts topics from a provided piece of wikimarkup
class TopicExtractor:
    
    def __init__(self, signature_timestamp_re=TIMESTAMP_RE,
                       max_topic_heading=2):
        self.signature_timestamp_re = signature_timestamp_re
        self.min_topic_heading = int(min_topic_heading)
    
    def extract(self, text):
        wikicode = mwp.parse(text)
        return parse_wikicode(wikicode)
    
    def extract_wikicode(self, wikicode, pos=0):
        """
        Extracts topics from Wikicode.  Returns a generator of 
        `Topic`
        """
        while pos < len(wikicode):
            
            if isinstance(wikicode[pos], mwp.nodes.Tag):
                # A tag can contain any amount of the page and needs 
                # to be treated like a first-order thing at this level. 
                tag = wikicode[pos]
                for pos, topic in self.extract_wikicode(tag):
                    yield topic
            elif isinstance(wikicode[pos], mwp.nodes.Heading):
                # We ran into a header.  If the header is small enough
                # then we suppose we ran into the beginning of a topic.
                heading = wikicode[pos]
                if heading.level >= self.min_topic_heading:
                    pos, topic = self._extract_topic(wikicode, pos)
                    yield topic
            else:
                # We ran into something that isn't a header or a tag.
                continue
            
            pos += 1
    
    def _extract_topic(self, wikicode, pos):
        """
        Extracts a single topic from Wikicode.  Returns a single
        topic.  Topic may lack content if there's nothing but a header
        """
        # We know that the first node is the header
        
        header = wikicode[pos]
        pos += 1
        
        topic = Topic(heading.title)
        
        while pos < len(wikicode):
            
            if isinstance(wikicode[pos], mwp.nodes.Header):
                next_header = wikicode[pos]
                if next_header.level < header.level:
                    # We've reached a sub-header.
                    topic.append(self._extract_topic(wikicode, pos))
                else:
                    # Same level or greater header.  We're done here.
                    return pos, topic
            else:
                post = self._extract_post(wikicode, pos)
                topic.append(post)
            
            pos += 1
    
    def _extract_post(self, wikicode, pos):
        """
        Extracts a post from the wiki code.
        """
        post = Post()
        
        while pos < len(wikicode):
            
            if isinstance(wikicode[pos], mwp.nodes.Header):
                # Can't read past a header
                return pos, post
            elif self.signature_timestamp_re.search(str(wikicode[pos])):
                # Found a signature!
                timestamp = self.signature_timestamp_re.search(str(wikicode[pos]))
                user_link = self._last_user_page_link(wikicode, pos)
                post.user_text = self._normalize_usertext(user_link)
                
                return pos, post
            else:
                post.append(node)
            
        
    def _last_user_page_link(self, wikicode, pos):
        """
        Gets the most recent link to User or User_talk before `pos`
        """
        raise NotImplementedError()
    
    def _normalize_usertext(self, link):
        """
        Extracts the user_text from a link.  
        """
        raise NotImplementedError()
