from xml.etree import ElementTree as ET

class NoteHtml(object): 
    @property
    def refs(self):
        html = []
        for ref in self.ref:
            html.append(f'<a href"#" data-bs-toggle="tooltip" data-bs-original-title="{ref.content}">{ref.fullkey}</a>')

        return ','.join(html)

    @property
    def fullkey_html(self):
        fkt = self.fullkeyto
        if "-" in fkt:
            fkt1,fkt2 = fkt.split("-")
            rec,num = fkt2.split(" ")
            fkt = f'{fkt1}-<span class="badge bg-secondary">{rec}</span> {num}'

        if len(self.receivers) > 1:
            return f'<span data-bs-toggle="tooltip" title="{self.receivers}">{fkt}</span>'
        else:
            return f'<span>{fkt}</span>'

    def read_html(self,reg,user):
        if self.rel_flow(reg) == 'out': # Only the in notes are read or unread
            return ""
        
        if self.is_read(user):
            a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Mark as read'})
            i = ET.Element('i',attrib={'class':'bi bi-eye','style':'color: gray;'})
        else:
            a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Mark as unread'})
            i = ET.Element('i',attrib={'class':'bi bi-eye-slash','style':'color: black;'})
        
        a.append(i)
        return ET.tostring(a,encoding='unicode',method='html')

    def done_html(self,reg,user):
        if self.rel_flow(reg) == 'out': # Only the in notes are read or unread
            return ""

        if (self.is_involve(user) and self.is_read(user) and self.state >= 4) or user.admin:
            if self.done == 1:
                a = ET.Element('a',attrib={'href':f'?reg={reg}&mark={self.id}','data-bs-toggle':'tooltip','title':'Mark as done'})
                i = ET.Element('i',attrib={'class':'bi bi-check-circle','style':'color: green;'})
            else:
                a = ET.Element('a',attrib={'href':f'?reg={reg}&mark={self.id}','data-bs-toggle':'tooltip','title':'Mark as to be done'})
                i = ET.Element('i',attrib={'class':'bi bi-x-circle','style':'color: red;'})
        else:
            a = ET.Element('span')
            if self.done == 1:
                i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: gray;'})
            else:
                i = ET.Element('i',attrib={'class':'bi bi-x','style':'color: gray;'})
        
        a.append(i)
        return ET.tostring(a,encoding='unicode',method='html')

    def state_html(self,reg,user):
        if self.rel_flow(reg) == 'in':
            return ""

        match self.state:
            case 0:
                a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Send note'})
                i = ET.Element('i',attrib={'class':'bi bi-send','style':'color: gray;'})
            case 1:
                a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Unsent note'})
                i = ET.Element('i',attrib={'class':'bi bi-send-fill','style':'color: gray;'})
            case w if w in [2,3]:
                a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Received in cr'})
                i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: gray;'})
            case 4:
                a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Working on it'})
                i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: blue;'})
            case 5:
                a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Done'})
                i = ET.Element('i',attrib={'class':'bi bi-check-all','style':'color: blue;'})

        a.append(i)
        return ET.tostring(a,encoding='unicode',method='html')



                
