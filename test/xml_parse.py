import xml.etree.ElementTree as ET

text = """
<select id="selectPostIn" resultType="domain.blog.Post">
  SELECT *
  FROM POST P
  WHERE ID in
  <foreach item="item" index="index" collection="list"
      open="(" separator="," close=")">
        #{item}
  </foreach>
  abc 
</select>
"""


def parse(text):
    root = ET.fromstring(text)
    traverse_xml_tree(root)


def traverse_xml_tree(node):
    if len(node.items()) > 0:
        for child in node:
            print(child.tag, child.attrib)
            traverse_xml_tree(child)


if __name__ == '__main__':
    parse(text)
