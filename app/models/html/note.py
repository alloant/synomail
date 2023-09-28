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
